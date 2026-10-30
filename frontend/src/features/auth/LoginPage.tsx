import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { z } from 'zod';
import { useAuth } from './AuthContext';
import { OtpStep } from './OtpStep';

const emailSchema = z
  .string()
  .trim()
  .min(1, 'Email address is required')
  .email('Please enter a valid institutional email address');

interface LocationState {
  from?: {
    pathname: string;
  };
}

export const LoginPage: React.FC = () => {
  const { user, isAuthenticated, requestOtp, verifyOtp, error, clearError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [step, setStep] = useState<'email' | 'otp'>('email');
  const [email, setEmail] = useState<string>('');
  const [emailError, setEmailError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // If already authenticated, redirect by role
  useEffect(() => {
    if (isAuthenticated && user) {
      const state = location.state as LocationState | undefined;
      const destination =
        state?.from?.pathname || (user.role === 'admin' ? '/admin' : '/faculty');
      navigate(destination, { replace: true });
    }
  }, [isAuthenticated, user, navigate, location.state]);

  const handleEmailSubmit = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    clearError();

    const parseResult = emailSchema.safeParse(email);
    if (!parseResult.success) {
      setEmailError(parseResult.error.errors[0]?.message ?? 'Invalid email address');
      return;
    }

    setEmailError(null);
    setIsLoading(true);

    try {
      await requestOtp(parseResult.data);
      setStep('otp');
    } catch {
      // Server error handled via context
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyOtp = async (otpCode: string): Promise<void> => {
    setIsLoading(true);
    try {
      const verifiedUser = await verifyOtp(email, otpCode);
      const state = location.state as LocationState | undefined;
      const destination =
        state?.from?.pathname || (verifiedUser.role === 'admin' ? '/admin' : '/faculty');
      navigate(destination, { replace: true });
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendOtp = async (): Promise<void> => {
    await requestOtp(email);
  };

  const handleQuickFill = (demoEmail: string): void => {
    setEmail(demoEmail);
    setEmailError(null);
    clearError();
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center p-4">
      {/* Background radial glow */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_var(--tw-gradient-stops))] from-blue-900/20 via-transparent to-transparent pointer-events-none" />

      <div className="relative max-w-md w-full bg-slate-900/90 border border-slate-800 rounded-2xl p-8 shadow-2xl backdrop-blur-sm">
        {step === 'email' ? (
          <div>
            <div className="text-center mb-8">
              <div className="inline-flex p-3 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 mb-3 font-mono text-xs font-semibold uppercase tracking-wider">
                Institutional Portal
              </div>
              <h1 className="text-2xl font-bold tracking-tight text-white">
                Workload System Sign In
              </h1>
              <p className="text-sm text-slate-400 mt-2">
                Passwordless one-time passcode login for Department Chairs and Faculty members.
              </p>
            </div>

            <form onSubmit={(e) => void handleEmailSubmit(e)} className="space-y-4" noValidate>
              <div>
                <label
                  htmlFor="email"
                  className="block text-xs font-medium text-slate-300 uppercase tracking-wider mb-2"
                >
                  University Email Address
                </label>
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (emailError) setEmailError(null);
                    if (error) clearError();
                  }}
                  disabled={isLoading}
                  placeholder="faculty@university.edu"
                  aria-invalid={Boolean(emailError || error)}
                  aria-describedby={emailError || error ? 'email-error' : undefined}
                  className={`w-full px-4 py-3 rounded-lg bg-slate-950 border ${
                    emailError || error
                      ? 'border-rose-500/80 text-rose-200 focus:border-rose-500'
                      : 'border-slate-700 text-white focus:border-blue-500'
                  } placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-blue-500 text-sm transition`}
                />
              </div>

              {(emailError || error) && (
                <div
                  id="email-error"
                  role="alert"
                  className="p-3 rounded-lg bg-rose-950/50 border border-rose-800/60 text-xs text-rose-300 flex items-start gap-2"
                >
                  <span className="text-base leading-none">⚠️</span>
                  <span>{emailError || error}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading || !email.trim()}
                className={`w-full py-3 px-4 rounded-lg font-medium text-sm transition flex items-center justify-center gap-2 ${
                  isLoading || !email.trim()
                    ? 'bg-blue-600/50 text-blue-200 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-600/30 cursor-pointer'
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
                    <span>Sending Passcode...</span>
                  </>
                ) : (
                  <span>Send One-Time Passcode (OTP)</span>
                )}
              </button>
            </form>

            {/* Quick-fill Demo Account Helpers */}
            <div className="mt-6 pt-5 border-t border-slate-800">
              <span className="block text-[11px] font-medium text-slate-400 uppercase tracking-wider mb-2.5">
                Quick Sign-In Test Accounts:
              </span>
              <div className="grid grid-cols-1 gap-2">
                <button
                  type="button"
                  onClick={() => handleQuickFill('admin@university.edu')}
                  className="w-full text-left p-2.5 rounded-lg bg-slate-950/60 hover:bg-slate-800/80 border border-slate-800 hover:border-blue-500/40 transition group cursor-pointer"
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono text-slate-300 group-hover:text-blue-300">
                      admin@university.edu
                    </span>
                    <span className="px-1.5 py-0.5 rounded text-[10px] bg-blue-500/10 text-blue-400 border border-blue-500/20 font-semibold">
                      ADMIN
                    </span>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => handleQuickFill('alan.turing@university.edu')}
                  className="w-full text-left p-2.5 rounded-lg bg-slate-950/60 hover:bg-slate-800/80 border border-slate-800 hover:border-purple-500/40 transition group cursor-pointer"
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono text-slate-300 group-hover:text-purple-300">
                      alan.turing@university.edu
                    </span>
                    <span className="px-1.5 py-0.5 rounded text-[10px] bg-purple-500/10 text-purple-400 border border-purple-500/20 font-semibold">
                      FACULTY (f-01)
                    </span>
                  </div>
                </button>
              </div>
            </div>
          </div>
        ) : (
          <OtpStep
            email={email}
            onVerify={handleVerifyOtp}
            onResend={handleResendOtp}
            onChangeEmail={() => {
              setStep('email');
              clearError();
            }}
            isLoading={isLoading}
            serverError={error}
          />
        )}

        <div className="mt-8 pt-6 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <Link to="/" className="text-blue-400 hover:text-blue-300 transition">
            &larr; Back to Landing Page
          </Link>
          <span className="text-slate-600 font-mono">v0.1.0</span>
        </div>
      </div>
    </div>
  );
};
