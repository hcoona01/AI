import { Link } from 'react-router-dom';

export const LoginPage = () => {
  return (
    <div className="min-h-[80vh] flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-slate-900/90 border border-slate-800 rounded-2xl p-8 shadow-2xl backdrop-blur-sm">
        <div className="text-center mb-8">
          <div className="inline-flex p-3 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 mb-3 font-mono text-sm font-semibold">
            SECURE ACCESS
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Institutional Sign In</h2>
          <p className="text-sm text-slate-400 mt-2">
            Passwordless Email OTP Authentication for Department Planners & Faculty
          </p>
        </div>

        <form onSubmit={(e) => e.preventDefault()} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-xs font-medium text-slate-300 uppercase tracking-wider mb-2">
              University Email Address
            </label>
            <input
              id="email"
              type="email"
              placeholder="faculty@university.edu"
              disabled
              className="w-full px-4 py-3 rounded-lg bg-slate-950 border border-slate-700 text-slate-400 placeholder-slate-600 focus:outline-none cursor-not-allowed text-sm"
            />
          </div>

          <button
            type="button"
            disabled
            className="w-full py-3 px-4 rounded-lg bg-blue-600/50 text-blue-200 font-medium text-sm cursor-not-allowed transition"
          >
            Send One-Time Passcode (OTP)
          </button>
        </form>

        <div className="mt-8 pt-6 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <Link to="/" className="text-blue-400 hover:text-blue-300 transition">
            &larr; Back to Landing Page
          </Link>
          <span className="text-slate-600">v0.1.0</span>
        </div>
      </div>
    </div>
  );
};
