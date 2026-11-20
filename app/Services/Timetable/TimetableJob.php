<?php

namespace App\Services\Timetable;

/**
 * One sync job = one private directory with source.xlsx, target.xlsx, meta.json and engine outputs
 * (DETAIL_DESIGN §11.1).
 */
class TimetableJob
{
    public function __construct(
        public readonly string $id,
        public readonly string $dir,
        public array $meta,
    ) {}

    public function path(string $file): string
    {
        return $this->dir.DIRECTORY_SEPARATOR.$file;
    }

    public function has(string $file): bool
    {
        return is_file($this->path($file));
    }

    public function readJson(string $file): ?array
    {
        return $this->has($file) ? json_decode(file_get_contents($this->path($file)), true) : null;
    }

    public function writeJson(string $file, array $data): void
    {
        $tmp = $this->path($file.'.tmp');
        file_put_contents($tmp, json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
        rename($tmp, $this->path($file));
    }

    /** Public view of the job (no paths, no owner). */
    public function summary(): array
    {
        return [
            'job_id' => $this->id,
            'status' => $this->meta['status'],
            'source_file_name' => $this->meta['source_file_name'],
            'target_file_name' => $this->meta['target_file_name'],
            'created_at' => $this->meta['created_at'],
            'expires_at' => $this->meta['expires_at'],
        ];
    }
}
