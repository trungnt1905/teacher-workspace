<?php

namespace App\Exceptions;

use Illuminate\Http\JsonResponse;
use RuntimeException;

/**
 * Business error rendered as {"success": false, "error": {code, message, details}} (DETAIL_DESIGN §9.6).
 * Messages are user-facing Vietnamese; details must never contain paths, traces or secrets.
 */
class ApiException extends RuntimeException
{
    public function __construct(
        public readonly string $errorCode,
        string $message,
        public readonly int $status = 422,
        public readonly array $details = [],
    ) {
        parent::__construct($message);
    }

    public static function body(string $code, string $message, array $details = []): array
    {
        return ['success' => false, 'error' => ['code' => $code, 'message' => $message, 'details' => (object) $details]];
    }

    public function render(): JsonResponse
    {
        return response()->json(self::body($this->errorCode, $this->getMessage(), $this->details), $this->status);
    }
}
