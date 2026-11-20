<?php

// Timetable sync settings (DETAIL_DESIGN §11, §13.3, §13.6).

$localVenv = base_path('python/.venv/bin/python');

return [
    // Docker/Render sets PYTHON_BINARY; locally the project venv is used when it exists.
    'python_binary' => env('PYTHON_BINARY') ?: (is_file($localVenv) ? $localVenv : 'python3'),

    'python_script' => env('TIMETABLE_PYTHON_SCRIPT', base_path('python/process_timetable.py')),

    'temp_root' => env('TIMETABLE_TEMP_ROOT', storage_path('app/private/timetable-jobs')),

    'max_file_size_mb' => (int) env('TIMETABLE_MAX_FILE_SIZE_MB', 5),

    'job_ttl_minutes' => (int) env('TIMETABLE_JOB_TTL_MINUTES', 60),

    'max_jobs' => (int) env('TIMETABLE_MAX_JOBS', 5),

    'process_timeout' => (int) env('TIMETABLE_PROCESS_TIMEOUT', 60),
];
