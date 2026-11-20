<?php

namespace App\Services\Timetable;

use App\Exceptions\ApiException;
use Illuminate\Process\Exceptions\ProcessTimedOutException;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Process;

/**
 * Runs python/process_timetable.py for one job (contract: DETAIL_DESIGN §8.3).
 *
 * Exit 0 -> result JSON file; exit 1 -> business error in the result file; anything else or a
 * timeout -> system error. Python logs (stderr, JSON lines) are forwarded to the Laravel log.
 */
class PythonEngine
{
    public const RESULT_FILES = [
        'list-weeks' => 'weeks.json',
        'analyze' => 'analysis.json',
        'generate' => 'generate.json',
    ];

    /** Business errors that mean "redo an earlier step" rather than "bad input". */
    private const CONFLICT_CODES = ['ANALYSIS_OUTDATED'];

    public function run(string $command, TimetableJob $job): array
    {
        $resultFile = self::RESULT_FILES[$command];
        $started = microtime(true);

        try {
            $result = Process::path(dirname(config('timetable.python_script')))
                ->timeout(config('timetable.process_timeout'))
                ->run([
                    config('timetable.python_binary'),
                    config('timetable.python_script'),
                    $command,
                    '--job-dir',
                    $job->dir,
                ]);
        } catch (ProcessTimedOutException) {
            Log::warning('timetable.python_timeout', ['job_id' => $job->id, 'command' => $command]);
            throw new ApiException('PROCESSING_TIMEOUT', 'Xử lý quá lâu, vui lòng thử lại với ít tuần hơn.', 504);
        }

        $context = [
            'job_id' => $job->id,
            'command' => $command,
            'exit_code' => $result->exitCode(),
            'duration_ms' => (int) ((microtime(true) - $started) * 1000),
        ];
        foreach (array_filter(explode("\n", $result->errorOutput())) as $line) {
            Log::info('timetable.python', $context + ['python' => json_decode($line, true) ?? $line]);
        }

        $payload = $job->readJson($resultFile);

        if ($result->exitCode() === 0 && is_array($payload) && ($payload['success'] ?? false)) {
            return $payload;
        }

        if ($result->exitCode() === 1 && isset($payload['error']['code'])) {
            $error = $payload['error'];
            $status = in_array($error['code'], self::CONFLICT_CODES, true) ? 409 : 422;
            throw new ApiException($error['code'], $error['message'], $status, $error['details'] ?? []);
        }

        Log::error('timetable.python_failed', $context);
        throw new ApiException('PROCESSING_FAILED', 'Có lỗi hệ thống khi xử lý file, vui lòng thử lại.', 500);
    }
}
