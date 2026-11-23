<?php

namespace App\Http\Controllers\Api;

use App\Exceptions\ApiException;
use App\Http\Controllers\Controller;
use App\Http\Requests\TimetableSelectionRequest;
use App\Services\Timetable\JobStore;
use App\Services\Timetable\PythonEngine;
use App\Services\Timetable\TimetableJob;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Http\UploadedFile;
use Symfony\Component\HttpFoundation\BinaryFileResponse;

/** Timetable sync endpoints (DETAIL_DESIGN §9). All routes require authentication. */
class TimetableJobController extends Controller
{
    private const XLSX_MIME = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';

    public function __construct(
        private readonly JobStore $jobs,
        private readonly PythonEngine $engine,
    ) {}

    public function store(Request $request): JsonResponse
    {
        $maxKb = config('timetable.max_file_size_mb') * 1024;
        $request->validate([
            'source_file' => ['required', 'file', 'extensions:xlsx', "max:{$maxKb}"],
            'target_file' => ['required', 'file', 'extensions:xlsx', "max:{$maxKb}"],
        ], [
            'source_file.required' => 'Chưa chọn file nguồn.',
            'target_file.required' => 'Chưa chọn file đích.',
            '*.extensions' => 'Chỉ hỗ trợ file .xlsx.',
            '*.max' => 'File vượt quá '.config('timetable.max_file_size_mb').'MB.',
        ]);

        foreach (['source_file' => 'File nguồn', 'target_file' => 'File đích'] as $field => $label) {
            $this->assertZipSignature($request->file($field), $label);
        }

        $job = $this->jobs->create($this->owner($request), $request->file('source_file'), $request->file('target_file'));

        try {
            $weeks = $this->engine->run('list-weeks', $job);
        } catch (ApiException $e) {
            $this->jobs->delete($job); // unusable upload: do not keep the files around
            throw $e;
        }

        return response()->json(['success' => true, 'data' => $job->summary() + $this->weeksData($weeks)], 201);
    }

    public function show(Request $request, string $job): JsonResponse
    {
        $job = $this->jobs->find($job, $this->owner($request));

        return response()->json(['success' => true, 'data' => $job->summary() + $this->weeksData($job->readJson('weeks.json') ?? [])]);
    }

    public function analyze(TimetableSelectionRequest $request, string $job): JsonResponse
    {
        $job = $this->jobs->find($job, $this->owner($request));

        $analysis = $this->jobs->withLock($job, function () use ($job, $request) {
            $job->writeJson('request.json', $request->engineRequest());
            $job->has('result.xlsx') && unlink($job->path('result.xlsx'));
            $analysis = $this->engine->run('analyze', $job);
            $this->jobs->update($job, ['status' => 'preview_ready']);

            return $analysis;
        });

        // `writes` is the engine's internal edit list; the UI only needs the mapping.
        $analysis['weeks'] = array_map(fn ($w) => array_diff_key($w, ['writes' => true]), $analysis['weeks']);
        unset($analysis['success'], $analysis['source_sha256'], $analysis['target_sha256']);

        return response()->json(['success' => true, 'data' => ['job_id' => $job->id] + $analysis]);
    }

    public function generate(TimetableSelectionRequest $request, string $job): JsonResponse
    {
        $job = $this->jobs->find($job, $this->owner($request));

        $summary = $this->jobs->withLock($job, function () use ($job, $request) {
            $job->writeJson('request.json', $request->engineRequest());
            $summary = $this->engine->run('generate', $job);
            $this->jobs->update($job, ['status' => 'completed']);

            return $summary;
        });

        return response()->json(['success' => true, 'data' => [
            'job_id' => $job->id,
            'file_name' => $this->resultFileName($job),
            'download_url' => url("/api/v1/timetable/jobs/{$job->id}/download"),
            'weeks_filled' => $summary['weeks_filled'],
            'cells_written' => $summary['cells_written'],
            'renamed_sheets' => $summary['renamed_sheets'] ?? [],
            'manual_todo' => $summary['manual_todo'],
        ]]);
    }

    public function download(Request $request, string $job): BinaryFileResponse
    {
        $job = $this->jobs->find($job, $this->owner($request));

        if (! $job->has('result.xlsx')) {
            throw new ApiException('RESULT_NOT_READY', 'Chưa có file kết quả, vui lòng tạo file trước.', 404);
        }

        // Kept until the job expires so the teacher can download again (DETAIL_DESIGN §11.4).
        return response()->download($job->path('result.xlsx'), $this->resultFileName($job), [
            'Content-Type' => self::XLSX_MIME,
            'Cache-Control' => 'no-store, private',
            'X-Content-Type-Options' => 'nosniff',
        ]);
    }

    public function destroy(Request $request, string $job): JsonResponse
    {
        $this->jobs->delete($this->jobs->find($job, $this->owner($request)));

        return response()->json(['success' => true]);
    }

    private function owner(Request $request): string
    {
        return (string) $request->user()->getAuthIdentifier();
    }

    private function assertZipSignature(UploadedFile $file, string $label): void
    {
        $handle = fopen($file->getRealPath(), 'rb');
        $magic = fread($handle, 4);
        fclose($handle);

        if ($magic !== "PK\x03\x04") {
            throw new ApiException('INVALID_FILE_TYPE', "{$label} không đúng định dạng .xlsx.", 422, ['file' => $label]);
        }
    }

    private function weeksData(array $weeks): array
    {
        return [
            'weeks' => $weeks['weeks'] ?? [],
            'subjects' => $weeks['subjects'] ?? [],
            'default_selected_subjects' => $weeks['default_selected_subjects'] ?? [],
            'days' => $weeks['days'] ?? [],
            // One-sheet target (e.g. a file made from the template): one week per run.
            'single_target_sheet' => $weeks['single_target_sheet'] ?? null,
            'max_weeks' => $weeks['max_weeks'] ?? null,
        ];
    }

    /** "<target name>_dongbo_<yyyymmdd-hhmm>.xlsx" (DETAIL_DESIGN §9.5). */
    private function resultFileName(TimetableJob $job): string
    {
        $base = pathinfo($job->meta['target_file_name'], PATHINFO_FILENAME) ?: 'lich-bao-giang';

        return $base.'_dongbo_'.now()->format('Ymd-Hi').'.xlsx';
    }
}
