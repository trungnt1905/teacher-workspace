<?php

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;

/**
 * Body of analyze/generate (DETAIL_DESIGN §9.3): which weeks, which subjects, manual day-off overrides.
 * Generate must send exactly what was analyzed; the engine rejects anything else (ANALYSIS_OUTDATED).
 */
class TimetableSelectionRequest extends FormRequest
{
    public function rules(): array
    {
        // Day labels come from the same profile the engine uses (no hardcoded layout).
        $profile = json_decode(file_get_contents(base_path('python/config/template_profile.json')), true);
        $days = array_column($profile['days'], 'label');
        $sessions = array_keys($profile['days'][0]['sessions']);

        return [
            'weeks' => ['required', 'array', 'min:1', 'max:60'],
            'weeks.*' => ['integer', 'between:1,99', 'distinct'],
            'selected_subjects' => ['required', 'array', 'min:1', 'max:50'],
            'selected_subjects.*' => ['string', 'max:100', 'distinct'],
            'manual_days_off' => ['sometimes', 'array', 'max:100'],
            'manual_days_off.*.week_number' => ['required', 'integer', 'between:1,99'],
            'manual_days_off.*.day' => ['required', 'string', Rule::in($days)],
            'manual_days_off.*.session' => ['nullable', 'string', Rule::in($sessions)],
            'manual_days_off.*.is_day_off' => ['required', 'boolean'],
        ];
    }

    public function messages(): array
    {
        return [
            'weeks.required' => 'Chưa chọn tuần nào.',
            'weeks.min' => 'Chưa chọn tuần nào.',
            'selected_subjects.required' => 'Chưa chọn môn nào để đồng bộ.',
            'selected_subjects.min' => 'Chưa chọn môn nào để đồng bộ.',
        ];
    }

    /** Normalized payload written to request.json for the engine. */
    public function engineRequest(): array
    {
        $data = $this->validated();

        return [
            'weeks' => array_map('intval', $data['weeks']),
            'selected_subjects' => array_values($data['selected_subjects']),
            'manual_days_off' => array_map(fn ($m) => array_filter([
                'week_number' => (int) $m['week_number'],
                'day' => $m['day'],
                'session' => $m['session'] ?? null,
                'is_day_off' => (bool) $m['is_day_off'],
            ], fn ($v) => $v !== null), $data['manual_days_off'] ?? []),
        ];
    }
}
