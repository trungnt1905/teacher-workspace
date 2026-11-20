<?php

namespace App\Services\Timetable;

use App\Exceptions\ApiException;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\File;
use Illuminate\Support\Str;

/**
 * Temporary job directories under config('timetable.temp_root') (DETAIL_DESIGN §11).
 *
 * Nothing here is durable: Render Free loses the filesystem when it sleeps, so a missing job is a
 * normal situation reported as JOB_NOT_FOUND ("upload again"), never a server error.
 */
class JobStore
{
    public const META = 'meta.json';

    public function root(): string
    {
        return config('timetable.temp_root');
    }

    public function create(string $owner, UploadedFile $source, UploadedFile $target): TimetableJob
    {
        $this->purgeExpired();
        $this->enforceLimit();

        $id = (string) Str::uuid();
        $dir = $this->root().DIRECTORY_SEPARATOR.$id;
        File::ensureDirectoryExists($dir, 0700);

        $source->move($dir, 'source.xlsx');
        $target->move($dir, 'target.xlsx');

        $now = now();
        $job = new TimetableJob($id, $dir, [
            'job_id' => $id,
            'owner' => $owner,
            'created_at' => $now->toIso8601String(),
            'expires_at' => $now->copy()->addMinutes(config('timetable.job_ttl_minutes'))->toIso8601String(),
            'status' => 'uploaded',
            'source_file_name' => self::displayName($source->getClientOriginalName()),
            'target_file_name' => self::displayName($target->getClientOriginalName()),
            'source_sha256' => hash_file('sha256', $dir.'/source.xlsx'),
            'target_sha256' => hash_file('sha256', $dir.'/target.xlsx'),
        ]);
        $job->writeJson(self::META, $job->meta);

        return $job;
    }

    public function find(string $id, string $owner): TimetableJob
    {
        $notFound = new ApiException('JOB_NOT_FOUND', 'Phiên xử lý đã hết hạn hoặc không tồn tại, vui lòng upload lại.', 404);

        if (! Str::isUuid($id)) {
            throw $notFound;
        }

        $dir = $this->root().DIRECTORY_SEPARATOR.$id;
        $meta = is_file($dir.'/'.self::META) ? json_decode(file_get_contents($dir.'/'.self::META), true) : null;

        // Another owner's job is reported exactly like a missing one.
        if (! is_array($meta) || ($meta['owner'] ?? null) !== $owner) {
            throw $notFound;
        }

        $job = new TimetableJob($id, $dir, $meta);
        if ($this->isExpired($job)) {
            $this->delete($job);
            throw $notFound;
        }

        return $job;
    }

    public function update(TimetableJob $job, array $changes): void
    {
        $job->meta = array_merge($job->meta, $changes);
        $job->writeJson(self::META, $job->meta);
    }

    public function delete(TimetableJob $job): void
    {
        File::deleteDirectory($job->dir);
    }

    /**
     * Run $callback while holding an exclusive lock on the job, so the same job is never
     * analyzed/generated twice at the same time (DETAIL_DESIGN §10.3).
     */
    public function withLock(TimetableJob $job, callable $callback): mixed
    {
        $handle = fopen($job->path('.lock'), 'c');
        if (! flock($handle, LOCK_EX | LOCK_NB)) {
            fclose($handle);
            throw new ApiException('JOB_BUSY', 'Phiên xử lý đang chạy, vui lòng đợi.', 409);
        }

        try {
            return $callback();
        } finally {
            flock($handle, LOCK_UN);
            fclose($handle);
        }
    }

    public function purgeExpired(): void
    {
        foreach ($this->all() as $job) {
            if ($this->isExpired($job)) {
                $this->delete($job);
            }
        }
    }

    /** Keep at most max_jobs directories: make room for one more by deleting the oldest. */
    private function enforceLimit(): void
    {
        $jobs = $this->all();
        usort($jobs, fn ($a, $b) => strcmp($a->meta['created_at'] ?? '', $b->meta['created_at'] ?? ''));
        $excess = count($jobs) - (config('timetable.max_jobs') - 1);
        foreach (array_slice($jobs, 0, max(0, $excess)) as $job) {
            $this->delete($job);
        }
    }

    /** @return TimetableJob[] */
    private function all(): array
    {
        if (! is_dir($this->root())) {
            return [];
        }

        $jobs = [];
        foreach (File::directories($this->root()) as $dir) {
            $meta = is_file($dir.'/'.self::META) ? json_decode(file_get_contents($dir.'/'.self::META), true) : null;
            // Directories without readable meta are leftovers from a crash: treat as expired.
            $jobs[] = new TimetableJob(basename($dir), $dir, is_array($meta) ? $meta : ['expires_at' => '1970-01-01T00:00:00+00:00']);
        }

        return $jobs;
    }

    private function isExpired(TimetableJob $job): bool
    {
        return now()->greaterThanOrEqualTo($job->meta['expires_at'] ?? '1970-01-01T00:00:00+00:00');
    }

    /** Client file names are only shown back to the user; strip paths and control characters. */
    public static function displayName(string $name): string
    {
        $name = basename(str_replace('\\', '/', $name));
        $name = preg_replace('/[\x00-\x1F\x7F]/u', '', $name) ?? '';

        return Str::limit($name !== '' ? $name : 'file.xlsx', 120, '');
    }
}
