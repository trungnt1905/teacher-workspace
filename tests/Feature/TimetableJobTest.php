<?php

namespace Tests\Feature;

use Illuminate\Auth\GenericUser;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\File;
use Illuminate\Testing\TestResponse;
use Tests\TestCase;
use ZipArchive;

/**
 * Full API flow against the real Python engine and the teacher's sample workbooks
 * (python/tests/fixtures). Requires python/.venv (see README).
 */
class TimetableJobTest extends TestCase
{
    private const DEFAULT_SUBJECTS = ['Tiếng Việt', 'Toán', 'Khoa học', 'Đạo đức', 'HĐTN', 'HĐTN (SHL)', 'GDTC chung'];

    protected function setUp(): void
    {
        parent::setUp();
        $this->actingAs($this->admin());
    }

    /** Upload a copy of a fixture (UploadedFile::move would otherwise move the fixture itself). */
    private function fixture(string $name, ?string $clientName = null): UploadedFile
    {
        $copy = tempnam(sys_get_temp_dir(), 'tw');
        copy(base_path("python/tests/fixtures/{$name}"), $copy);

        return new UploadedFile($copy, $clientName ?? $name, null, null, true);
    }

    private function upload(?UploadedFile $source = null, ?UploadedFile $target = null): TestResponse
    {
        return $this->post('/api/v1/timetable/jobs', [
            'source_file' => $source ?? $this->fixture('lbg_mau.xlsx'),
            'target_file' => $target ?? $this->fixture('tuan8_lop_dich.xlsx', 'Lịch báo giảng 5B.xlsx'),
        ], ['Accept' => 'application/json']);
    }

    private function jobId(): string
    {
        return $this->upload()->assertCreated()->json('data.job_id');
    }

    private function selection(array $subjects = self::DEFAULT_SUBJECTS, array $weeks = [8]): array
    {
        return ['weeks' => $weeks, 'selected_subjects' => $subjects, 'manual_days_off' => []];
    }

    public function test_requires_authentication(): void
    {
        $this->app['auth']->guard('web')->logout();
        $this->postJson('/api/v1/timetable/jobs')->assertUnauthorized();
        $this->getJson('/api/v1/timetable/jobs/'.fake()->uuid())->assertUnauthorized();
    }

    public function test_upload_lists_weeks_and_subjects(): void
    {
        $response = $this->upload()->assertCreated()
            ->assertJsonPath('data.status', 'uploaded')
            ->assertJsonPath('data.target_file_name', 'Lịch báo giảng 5B.xlsx');

        $weeks = collect($response->json('data.weeks'))->keyBy('week_number');
        $this->assertSame('ready', $weeks[8]['target_status']);
        $this->assertTrue($weeks[8]['selectable']);
        $this->assertSame('missing', $weeks[7]['target_status']);
        $this->assertEqualsCanonicalizing(
            [...self::DEFAULT_SUBJECTS, 'HĐTN (SHDC)'],
            $response->json('data.default_selected_subjects'),
        );

        $this->assertSame(['Hai', 'Ba', 'Tư', 'Năm', 'Sáu'], array_column($response->json('data.days'), 'label'));

        $dir = "{$this->jobsRoot}/{$response->json('data.job_id')}";
        $this->assertFileExists("{$dir}/source.xlsx");
        $this->assertFileExists("{$dir}/meta.json");
        $this->assertArrayNotHasKey('owner', $response->json('data'));
    }

    public function test_upload_validation(): void
    {
        $this->post('/api/v1/timetable/jobs', ['source_file' => $this->fixture('lbg_mau.xlsx')], ['Accept' => 'application/json'])
            ->assertStatus(422)
            ->assertJsonPath('error.code', 'VALIDATION_FAILED')
            ->assertJsonPath('error.details.target_file.0', 'Chưa chọn file đích.');

        $this->upload(UploadedFile::fake()->create('lich.xls', 10))
            ->assertStatus(422)
            ->assertJsonPath('error.details.source_file.0', 'Chỉ hỗ trợ file .xlsx.');

        config(['timetable.max_file_size_mb' => 1]);
        $this->upload(UploadedFile::fake()->create('lon.xlsx', 2048))
            ->assertStatus(422)
            ->assertJsonPath('error.details.source_file.0', 'File vượt quá 1MB.');
    }

    public function test_renamed_non_zip_file_is_rejected_before_storing(): void
    {
        $this->upload(UploadedFile::fake()->createWithContent('gia.xlsx', 'not a workbook'))
            ->assertStatus(422)
            ->assertJsonPath('error.code', 'INVALID_FILE_TYPE');
        $this->assertDirectoryDoesNotExist($this->jobsRoot);
    }

    public function test_engine_business_error_on_upload_deletes_the_job(): void
    {
        $zip = tempnam(sys_get_temp_dir(), 'tw').'.xlsx';
        $archive = new ZipArchive;
        $archive->open($zip, ZipArchive::CREATE);
        $archive->addFromString('hello.txt', 'not an xlsx package');
        $archive->close();

        $this->upload(null, new UploadedFile($zip, 'dich.xlsx', null, null, true))
            ->assertStatus(422)
            ->assertJsonPath('error.code', 'INVALID_FILE_TYPE')
            ->assertJsonPath('error.message', 'File đích không đúng định dạng .xlsx.');
        $this->assertSame([], File::directories($this->jobsRoot));
    }

    public function test_full_flow_analyze_generate_download(): void
    {
        $id = $this->jobId();

        $analysis = $this->postJson("/api/v1/timetable/jobs/{$id}/analyze", $this->selection())->assertOk();
        $this->assertTrue($analysis->json('data.can_generate'));
        $week = $analysis->json('data.weeks.0');
        $this->assertArrayNotHasKey('writes', $week);
        $this->assertSame('matched', collect($week['subjects'])->firstWhere('subject', 'Toán')['status']);
        $this->getJson("/api/v1/timetable/jobs/{$id}")->assertJsonPath('data.status', 'preview_ready');

        $this->getJson("/api/v1/timetable/jobs/{$id}/download")->assertNotFound()->assertJsonPath('error.code', 'RESULT_NOT_READY');

        $generated = $this->postJson("/api/v1/timetable/jobs/{$id}/generate", $this->selection())->assertOk()
            ->assertJsonPath('data.weeks_filled', [8]);
        $this->assertStringStartsWith('Lịch báo giảng 5B_dongbo_', $generated->json('data.file_name'));

        $download = $this->get("/api/v1/timetable/jobs/{$id}/download")->assertOk()
            ->assertHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
        $this->assertStringContainsString('attachment;', $download->headers->get('Content-Disposition'));

        $zip = new ZipArchive;
        $this->assertTrue($zip->open($download->baseResponse->getFile()->getPathname()));
        $sheet = $zip->getFromName('xl/worksheets/sheet2.xml');
        $this->assertStringContainsString('Luyện tập chung (Tiết 1)', $sheet); // Toán, Wednesday in the target class
        $zip->close();

        // Downloading does not delete the file: the teacher can download again until the job expires.
        $this->get("/api/v1/timetable/jobs/{$id}/download")->assertOk();
    }

    public function test_generate_with_different_selection_is_rejected(): void
    {
        $id = $this->jobId();
        $this->postJson("/api/v1/timetable/jobs/{$id}/analyze", $this->selection())->assertOk();

        $this->postJson("/api/v1/timetable/jobs/{$id}/generate", $this->selection(['Toán']))
            ->assertStatus(409)
            ->assertJsonPath('error.code', 'ANALYSIS_OUTDATED');
    }

    public function test_generate_without_analyze(): void
    {
        $id = $this->jobId();
        $this->postJson("/api/v1/timetable/jobs/{$id}/generate", $this->selection())->assertStatus(409);
    }

    public function test_reanalyze_discards_previous_result(): void
    {
        $id = $this->jobId();
        $this->postJson("/api/v1/timetable/jobs/{$id}/analyze", $this->selection())->assertOk();
        $this->postJson("/api/v1/timetable/jobs/{$id}/generate", $this->selection())->assertOk();
        $this->postJson("/api/v1/timetable/jobs/{$id}/analyze", $this->selection(['Toán']))->assertOk();

        $this->getJson("/api/v1/timetable/jobs/{$id}/download")->assertJsonPath('error.code', 'RESULT_NOT_READY');
    }

    public function test_selection_validation(): void
    {
        $id = $this->jobId();
        $this->postJson("/api/v1/timetable/jobs/{$id}/analyze", ['weeks' => [], 'selected_subjects' => []])
            ->assertStatus(422)
            ->assertJsonPath('error.details.weeks.0', 'Chưa chọn tuần nào.');
        $this->postJson("/api/v1/timetable/jobs/{$id}/analyze", [
            ...$this->selection(), 'manual_days_off' => [['week_number' => 8, 'day' => 'Chủ nhật', 'is_day_off' => true]],
        ])->assertStatus(422);
    }

    public function test_manual_day_off_is_passed_to_engine(): void
    {
        $id = $this->jobId();
        $analysis = $this->postJson("/api/v1/timetable/jobs/{$id}/analyze", [
            ...$this->selection(), 'manual_days_off' => [['week_number' => 8, 'day' => 'Hai', 'is_day_off' => true]],
        ])->assertOk();

        $this->assertSame(['manual', 'manual'], array_column($analysis->json('data.weeks.0.days_off'), 'detected_by'));
        $this->assertSame('skipped_day_off', collect($analysis->json('data.weeks.0.subjects'))->firstWhere('subject', 'Toán')['status']);
    }

    public function test_jobs_of_another_owner_look_missing(): void
    {
        $id = $this->jobId();
        $this->actingAs(new GenericUser(['id' => 'someone-else', 'email' => 'x@example.com']));

        $this->getJson("/api/v1/timetable/jobs/{$id}")->assertNotFound()->assertJsonPath('error.code', 'JOB_NOT_FOUND');
        $this->get("/api/v1/timetable/jobs/{$id}/download", ['Accept' => 'application/json'])->assertNotFound();
        $this->deleteJson("/api/v1/timetable/jobs/{$id}")->assertNotFound();
        $this->assertDirectoryExists("{$this->jobsRoot}/{$id}");
    }

    public function test_invalid_job_id(): void
    {
        $this->getJson('/api/v1/timetable/jobs/../../etc')->assertNotFound();
        $this->getJson('/api/v1/timetable/jobs/not-a-uuid')->assertNotFound()->assertJsonPath('error.code', 'JOB_NOT_FOUND');
    }

    public function test_expired_job_is_deleted_and_reported_missing(): void
    {
        $id = $this->jobId();
        $this->travel(config('timetable.job_ttl_minutes') + 1)->minutes();

        $this->getJson("/api/v1/timetable/jobs/{$id}")->assertNotFound()->assertJsonPath('error.code', 'JOB_NOT_FOUND');
        $this->assertDirectoryDoesNotExist("{$this->jobsRoot}/{$id}");
    }

    public function test_job_count_is_limited(): void
    {
        config(['timetable.max_jobs' => 2]);
        $first = $this->jobId();
        $this->travel(1)->seconds();
        $second = $this->jobId();
        $this->travel(1)->seconds();
        $third = $this->jobId();

        $this->assertEqualsCanonicalizing([$second, $third], array_map('basename', File::directories($this->jobsRoot)));
        $this->getJson("/api/v1/timetable/jobs/{$first}")->assertNotFound();
    }

    public function test_destroy(): void
    {
        $id = $this->jobId();
        $this->deleteJson("/api/v1/timetable/jobs/{$id}")->assertOk();
        $this->assertDirectoryDoesNotExist("{$this->jobsRoot}/{$id}");
    }

    public function test_engine_crash_is_a_generic_500(): void
    {
        $id = $this->jobId();
        config(['timetable.python_script' => base_path('python/does_not_exist.py')]);

        $this->postJson("/api/v1/timetable/jobs/{$id}/analyze", $this->selection())
            ->assertStatus(500)
            ->assertJsonPath('error.code', 'PROCESSING_FAILED')
            ->assertJsonMissingPath('error.details.trace');
    }
}
