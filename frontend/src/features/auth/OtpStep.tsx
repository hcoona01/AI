import React, { useState, useEffect, useRef } from 'react';
import { z } from 'zod';

const otpSchema = z
  .string()
  .trim()
  .regex(/^\d{6}$/, 'Passcode must be exactly 6 digits');

export interface OtpStepProps {
  email: string;
  onVerify: (otp: string) => Promise<void>;
  onResend: () => Promise<void>;
  onChangeEmail: () => void;
  isLoading: boolean;
  serverError: string | null;
}

export const OtpStep: React.FC<OtpStepProps> = ({
  email,
  onVerify,
  onResend,
  onChangeEmail,
  isLoading,
  serverError,
}) => {
  const [otp, setOtp] = useState<string>('');
  const [validationError, setValidationError] = useState<string | null>(null);
  const [resendCooldown, setResendCooldown] = useState<number>(60);
  const [isResending, setIsResending] = useState<boolean>(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // 60-second countdown timer for resending OTP
  useEffect(() => {
    if (resendCooldown <= 0) return;

    const timer = setInterval(() => {
      setResendCooldown((prev) => Math.max(0, prev - 1));
    }, 1000);

    return () => clearInterval(timer);
  }, [resendCooldown]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleOtpChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    const rawVal = e.target.value.replace(/\D/g, '').slice(0, 6);
    setOtp(rawVal);
    setValidationError(null);

    // Auto-verify if 6 digits entered
    if (rawVal.length === 6 && !isLoading) {
      void handleSubmit(rawVal);
    }
  };

  const handleSubmit = async (codeToVerify?: string): Promise<void> => {
    const code = codeToVerify ?? otp;
    const result = otpSchema.safeParse(code);

    if (!result.success) {
      setValidationError(result.error.errors[0]?.message ?? 'Invalid 6-digit code');
      return;
    }

    setValidationError(null);
    try {
      await onVerify(result.data);
    } catch {
      // Error handled by parent / serverError state
    }
  };

  const handleResend = async (): Promise<void> => {
    if (resendCooldown > 0 || isResending) return;

    setIsResending(true);
    try {
      await onResend();
      setResendCooldown(60);
      setOtp('');
      inputRef.current?.focus();
    } catch {
      // Server error displayed via prop
    } finally {
      setIsResending(false);
    }
  };

  const displayError = validationError || serverError;

  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="pill mb-3">Step 2 of 2 · verification</div>
        <h2 className="text-2xl font-medium tracking-tight">Enter verification code</h2>
        <p className="text-sm text-slate-400 mt-2">
          We sent a 6-digit one-time passcode to{' '}
          <span className="text-slate-200 font-semibold">{email}</span>
        </p>
        <button
          type="button"
          onClick={onChangeEmail}
          className="text-xs text-blue-400 hover:underline underline-offset-4 mt-1 transition"
        >
          Change email address
        </button>
      </div>

      <div
        className="p-3.5 bg-[#e7efcf] border border-[#d5e0b0] rounded-2xl text-xs text-[#2c3a10] flex items-start gap-2.5"
        role="status"
      >
        <div>
          <strong className="font-semibold">Development mode:</strong> The one-time passcode is
          printed directly in your backend terminal console.
        </div>
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          void handleSubmit();
        }}
        className="space-y-4"
        noValidate
      >
        <div>
          <label
            htmlFor="otp-code"
            className="block text-xs font-medium text-slate-300 uppercase tracking-wider mb-2 text-center"
          >
            6-Digit One-Time Passcode
          </label>
          <input
            ref={inputRef}
            id="otp-code"
            type="text"
            inputMode="numeric"
            pattern="[0-9]*"
            maxLength={6}
            value={otp}
            onChange={handleOtpChange}
            disabled={isLoading}
            autoComplete="one-time-code"
            aria-label="6-Digit Verification Code"
            aria-invalid={Boolean(displayError)}
            aria-describedby={displayError ? 'otp-error' : undefined}
            placeholder="······"
            className={`w-full px-4 py-3 text-center text-3xl font-mono tracking-[0.5em] rounded-2xl bg-white border ${
              displayError
                ? 'border-rose-500/80 text-rose-700 focus:border-rose-500'
                : 'border-slate-700 text-slate-100 focus:border-blue-500'
            } placeholder-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-500 transition`}
          />
        </div>

        {displayError && (
          <div
            id="otp-error"
            role="alert"
            className="p-3 rounded-2xl bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-start gap-2"
          >
            <span className="text-base leading-none">⚠️</span>
            <span>{displayError}</span>
          </div>
        )}

        <button
          type="submit"
          disabled={isLoading || otp.length < 6}
          className={`btn w-full ${
            isLoading || otp.length < 6 ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        >
          {isLoading ? (
            <>
              <svg
                className="animate-spin h-4 w-4 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              <span>Verifying Passcode...</span>
            </>
          ) : (
            <span>Verify & Sign In</span>
          )}
        </button>
      </form>

      <div className="pt-2 text-center">
        {resendCooldown > 0 ? (
          <p className="text-xs text-slate-400">
            Resend available in{' '}
            <span className="font-mono text-slate-200 font-semibold">{resendCooldown}s</span>
          </p>
        ) : (
          <button
            type="button"
            onClick={() => void handleResend()}
            disabled={isResending}
            className="text-xs text-blue-400 hover:underline font-medium transition cursor-pointer"
          >
            {isResending ? 'Sending new code...' : 'Resend One-Time Passcode'}
          </button>
        )}
      </div>
    </div>
  );
};
