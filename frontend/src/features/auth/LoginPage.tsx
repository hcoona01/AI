import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { z } from 'zod';
import { useAuth } from './AuthContext';
import { OtpStep } from './OtpStep';
import { BrandMark } from '../../components/brand/BrandMark';
import { DashboardBackground } from '../../components/layout/DashboardBackground';

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
    <div className="relative min-h-screen flex flex-col justify-center items-center p-4 overflow-hidden">
      <DashboardBackground />

      <div className="relative z-10 max-w-md w-full bg-white/90 backdrop-blur-xl border border-white/80 rounded-[28px] p-8 shadow-[0_24px_60px_rgba(40,60,15,0.14)]">
        {step === 'email' ? (
          <div>
            <div className="text-center mb-8">
              <Link to="/" className="brand justify-center mb-4" style={{ fontSize: 22 }}>
                <BrandMark />
                <span>workload</span>
              </Link>
              <div className="pill mb-3">Institutional portal</div>
              <h1 className="text-2xl font-medium tracking-tight" style={{ letterSpacing: '-0.03em' }}>
                Workload system sign in
              </h1>
              <p className="text-sm text-slate-500 mt-2">
                Passwordless one-time passcode login for department chairs and faculty.
              </p>
            </div>

            <form onSubmit={(e) => void handleEmailSubmit(e)} className="space-y-4" noValidate>
              <div>
                <label
                  htmlFor="email"
                  className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2"
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
                  className={`w-full px-4 py-3 rounded-2xl bg-white border ${
                    emailError || error
                      ? 'border-rose-500/80 text-rose-700 focus:border-rose-500'
                      : 'border-slate-300 text-black focus:border-[#4d6a10]'
                  } placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-[#4d6a10]/20 text-sm font-medium transition shadow-xs text-black`}
                  style={{ color: '#121410' }}
                />
              </div>

              {(emailError || error) && (
                <div
                  id="email-error"
                  role="alert"
                  className="p-3 rounded-2xl bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-start gap-2"
                >
                  <span>{emailError || error}</span>
                </div>
              )}

              <button type="submit" disabled={isLoading || !email.trim()} className="btn w-full">
                {isLoading ? 'Sending passcode...' : 'Send one-time passcode'}
              </button>
            </form>

            <div className="mt-6 pt-5 border-t border-slate-200">
              <span className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2.5">
                Quick sign-in test accounts
              </span>
              <div className="grid grid-cols-1 gap-2">
                <button
                  type="button"
                  onClick={() => handleQuickFill('admin@university.edu')}
                  className="w-full text-left p-3 rounded-2xl bg-white/80 hover:bg-white border border-slate-200 hover:border-[#b4cd52] transition cursor-pointer shadow-xs"
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono text-slate-700 font-medium">admin@university.edu</span>
                    <span className="pill">Admin</span>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => handleQuickFill('alan.turing@university.edu')}
                  className="w-full text-left p-3 rounded-2xl bg-white/80 hover:bg-white border border-slate-200 hover:border-[#b4cd52] transition cursor-pointer shadow-xs"
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono text-slate-700 font-medium">alan.turing@university.edu</span>
                    <span className="pill">Faculty (f-01)</span>
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

        <div className="mt-8 pt-6 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
          <Link to="/" className="hover:underline flex items-center gap-1 font-medium">
            <span>←</span> Back to landing
          </Link>
          <span className="font-mono">v0.1.0</span>
        </div>
      </div>
    </div>
  );
};
