<?php

use App\Exceptions\ApiException;
use Illuminate\Auth\AuthenticationException;
use Illuminate\Cookie\Middleware\AddQueuedCookiesToResponse;
use Illuminate\Cookie\Middleware\EncryptCookies;
use Illuminate\Foundation\Application;
use Illuminate\Foundation\Configuration\Exceptions;
use Illuminate\Foundation\Configuration\Middleware;
use Illuminate\Foundation\Http\Middleware\PreventRequestForgery;
use Illuminate\Http\Exceptions\PostTooLargeException;
use Illuminate\Http\Exceptions\ThrottleRequestsException;
use Illuminate\Http\Request;
use Illuminate\Session\Middleware\StartSession;
use Illuminate\Validation\ValidationException;
use Symfony\Component\HttpKernel\Exception\HttpExceptionInterface;

return Application::configure(basePath: dirname(__DIR__))
    ->withRouting(
        web: __DIR__.'/../routes/web.php',
        api: __DIR__.'/../routes/api.php',
        commands: __DIR__.'/../routes/console.php',
        apiPrefix: 'api/v1',
    )
    ->withMiddleware(function (Middleware $middleware): void {
        // Render terminates HTTPS at its proxy; the container is only reachable through it.
        // Needed for the real client IP (login rate limit), https URLs and Secure cookies.
        $middleware->trustProxies(at: '*');

        // The SPA and the API share one origin, so the API uses the normal cookie session + CSRF
        // protection (DETAIL_DESIGN §12.1). Axios sends X-XSRF-TOKEN from the XSRF-TOKEN cookie.
        $middleware->api(prepend: [
            EncryptCookies::class,
            AddQueuedCookiesToResponse::class,
            StartSession::class,
            PreventRequestForgery::class,
        ]);
    })
    ->withExceptions(function (Exceptions $exceptions): void {
        $exceptions->shouldRenderJsonWhen(
            fn (Request $request) => $request->is('api/*') || $request->expectsJson(),
        );

        // Expected business outcomes (wrong password, expired job, mismatched selection…) are
        // answered to the user, not logged as errors. Engine/system failures are logged separately.
        $exceptions->dontReport([ApiException::class]);

        // Uniform API error body (DETAIL_DESIGN §9.6). No traces, paths or server details.
        $exceptions->render(function (Throwable $e, Request $request) {
            if (! $request->is('api/*') || $e instanceof ApiException) {
                return null;
            }

            [$status, $code, $message, $details] = match (true) {
                $e instanceof ValidationException => [422, 'VALIDATION_FAILED', 'Dữ liệu gửi lên không hợp lệ.', $e->errors()],
                $e instanceof AuthenticationException => [401, 'UNAUTHENTICATED', 'Vui lòng đăng nhập.', []],
                $e instanceof ThrottleRequestsException => [429, 'TOO_MANY_ATTEMPTS', 'Thử quá nhiều lần, vui lòng đợi một phút.', []],
                $e instanceof PostTooLargeException => [413, 'FILE_TOO_LARGE', 'File vượt quá dung lượng cho phép.', []],
                $e instanceof HttpExceptionInterface && $e->getStatusCode() === 419 => [419, 'CSRF_TOKEN_MISMATCH', 'Phiên làm việc đã hết hạn, vui lòng tải lại trang.', []],
                $e instanceof HttpExceptionInterface && $e->getStatusCode() === 404 => [404, 'NOT_FOUND', 'Không tìm thấy.', []],
                $e instanceof HttpExceptionInterface => [$e->getStatusCode(), 'HTTP_ERROR', 'Yêu cầu không hợp lệ.', []],
                default => [500, 'SERVER_ERROR', 'Có lỗi hệ thống, vui lòng thử lại.', []],
            };

            if ($status === 500 && config('app.debug')) {
                return null; // keep Laravel's debug page locally
            }

            return response()->json(ApiException::body($code, $message, $details), $status);
        });
    })->create();
