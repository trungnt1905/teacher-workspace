<?php

namespace App\Auth;

use Illuminate\Auth\GenericUser;
use Illuminate\Contracts\Auth\Authenticatable;
use Illuminate\Contracts\Auth\UserProvider;
use Illuminate\Contracts\Hashing\Hasher;

/**
 * Single pre-provisioned account read from the environment (DETAIL_DESIGN §12.1).
 * No database: ADMIN_EMAIL + ADMIN_PASSWORD_HASH (bcrypt/argon2, never plaintext).
 */
class EnvUserProvider implements UserProvider
{
    public const USER_ID = 'admin';

    public function __construct(
        private readonly Hasher $hasher,
        private readonly ?string $email,
        private readonly ?string $passwordHash,
    ) {}

    private function configured(): bool
    {
        return filled($this->email) && filled($this->passwordHash);
    }

    private function user(): GenericUser
    {
        return new GenericUser([
            'id' => self::USER_ID,
            'email' => $this->email,
            'name' => $this->email,
            'password' => $this->passwordHash,
            'remember_token' => null,
        ]);
    }

    public function retrieveById($identifier): ?Authenticatable
    {
        return $this->configured() && $identifier === self::USER_ID ? $this->user() : null;
    }

    public function retrieveByToken($identifier, #[\SensitiveParameter] $token): ?Authenticatable
    {
        return null; // "remember me" is not supported
    }

    public function updateRememberToken(Authenticatable $user, #[\SensitiveParameter] $token): void {}

    public function retrieveByCredentials(#[\SensitiveParameter] array $credentials): ?Authenticatable
    {
        $email = mb_strtolower(trim((string) ($credentials['email'] ?? '')));

        if (! $this->configured() || ! hash_equals(mb_strtolower($this->email), $email)) {
            return null;
        }

        return $this->user();
    }

    public function validateCredentials(Authenticatable $user, #[\SensitiveParameter] array $credentials): bool
    {
        return $this->hasher->check((string) ($credentials['password'] ?? ''), $user->getAuthPassword());
    }

    public function rehashPasswordIfRequired(Authenticatable $user, #[\SensitiveParameter] array $credentials, bool $force = false): void
    {
        // The hash lives in the environment; it cannot be rewritten at runtime.
    }
}
