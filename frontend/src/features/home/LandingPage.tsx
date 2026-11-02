import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchHealth, HealthResponse } from '../../lib/apiClient';
import { useAuth } from '../auth/AuthContext';
import { BrandMark } from '../../components/brand/BrandMark';
import { CLOUD_A, CLOUD_B, HERO_POSTER, HERO_VIDEO, NIGHT, TREE } from '../../lib/visualAssets';

const GLASS_POS: Array<[number, number]> = [
  [3, 64],
  [3, 71],
  [6.5, 71],
  [10, 71],
  [3, 78],
  [-1, 70],
  [45.5, 76],
  [49, 80],
  [49, 76],
  [52.5, 76],
  [86, 58],
  [86, 67],
  [82, 76],
  [89.5, 76],
  [86, 84],
];

const STAT_CARDS = [
  { label: 'Load fairness gain', to: 40, dec: 0, suf: '%' },
  { label: 'Faculty on roster', to: 300, dec: 0, suf: '+' },
  { label: 'Hard-constraint pass', to: 99.2, dec: 1, suf: '%' },
  { label: 'Forecast coverage', to: 99.2, dec: 1, suf: '%' },
] as const;

const LOOP_STEPS = [
  {
    num: '1',
    title: 'Demand comes in',
    body: 'Quantile forecasts (P10 / P50 / P90) estimate section sizes so chairs can plan against both quiet terms and enrollment surges.',
    cloud: CLOUD_B,
  },
  {
    num: '2',
    title: 'Solver assigns load',
    body: 'CP-SAT matches expertise tags to syllabi, respects max load and time clashes, then scores fairness with Gini and max–min gap.',
    cloud: CLOUD_A,
  },
  {
    num: '3',
    title: 'Humans take the crunch',
    body: 'Chairs override only when needed. Every change keeps a reason, re-validates hard rules, and lands on the audit trail.',
    cloud: CLOUD_B,
  },
] as const;

const ENGINE_MARKS = ['LightGBM', 'OR-Tools', 'CP-SAT', 'Gini', 'OTP'] as const;

interface PetalSpec {
  left: string;
  dx: string;
  duration: string;
  delay: string;
  scale: number;
}

interface GridSquare {
  left: string;
  top: string;
  delay: string;
  repeatDelay: string;
}

function makeSquares(count: number): GridSquare[] {
  return Array.from({ length: count }, () => {
    const col = Math.floor(Math.random() * 30);
    const row = Math.floor(Math.random() * 6);
    return {
      left: `${col * 48 - 10}px`,
      top: `${row * 48 + 6}px`,
      delay: `${Math.random() * 4}s`,
      repeatDelay: `${Math.random() * 3}s`,
    };
  });
}

function makePetals(): PetalSpec[] {
  return Array.from({ length: 18 }, () => ({
    left: `${Math.random() * 100}%`,
    dx: `${Math.round(Math.random() * 160 - 80)}px`,
    duration: `${9 + Math.random() * 9}s`,
    delay: `${-Math.random() * 15}s`,
    scale: 0.6 + Math.random() * 0.8,
  }));
}

function SplitHeadline({
  children,
  className,
  as: Tag = 'h2',
  id,
}: {
  children: React.ReactNode;
  className?: string;
  as?: 'h1' | 'h2';
  id?: string;
}): React.JSX.Element {
  const wrapRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    const root = wrapRef.current;
    if (!root || root.dataset.split === '1') return;
    root.dataset.split = '1';
    const walk = (node: Node): void => {
      const kids = Array.from(node.childNodes);
      kids.forEach((child) => {
        if (child.nodeType === Node.TEXT_NODE) {
          const text = child.textContent ?? '';
          if (!text.trim()) return;
          const frag = document.createDocumentFragment();
          text.split(/(\s+)/).forEach((part) => {
            if (!part) return;
            if (/^\s+$/.test(part)) {
              frag.appendChild(document.createTextNode(part));
              return;
            }
            const span = document.createElement('span');
            span.className = 'w';
            span.textContent = part;
            frag.appendChild(span);
          });
          node.replaceChild(frag, child);
        } else if (child.nodeType === Node.ELEMENT_NODE) {
          const el = child as HTMLElement;
          if (el.tagName !== 'BR') walk(child);
        }
      });
    };
    walk(root);
  }, []);

  return (
    <Tag ref={wrapRef} id={id} className={className}>
      {children}
    </Tag>
  );
}

export const LandingPage = (): React.JSX.Element => {
  const { user, isAuthenticated } = useAuth();
  const dashboardLink = user?.role === 'admin' ? '/admin' : '/faculty';
  const ctaHref = isAuthenticated ? dashboardLink : '/login';
  const ctaLabel = isAuthenticated ? 'Open planner' : 'Sign in to plan';

  const { data: health } = useQuery<HealthResponse, Error>({
    queryKey: ['health'],
    queryFn: fetchHealth,
    refetchInterval: 10000,
  });

  const [activePanel, setActivePanel] = useState<number>(0);
  const [countersOn, setCountersOn] = useState<boolean>(false);
  const [progress, setProgress] = useState<number>(0);
  const [introReady, setIntroReady] = useState<boolean>(false);
  const [footerPlay, setFooterPlay] = useState<boolean>(false);
  const [isMobile, setIsMobile] = useState<boolean>(
    typeof window !== 'undefined' ? window.innerWidth <= 760 : false,
  );

  const statsSquares = useMemo(() => makeSquares(22), []);
  const ctaSquares = useMemo(() => makeSquares(16), []);
  const petals = useMemo(() => makePetals(), []);
  const reducedMotion = useMemo(
    () =>
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    [],
  );

  const statsRef = useRef<HTMLElement>(null);
  const footerRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const onResize = (): void => setIsMobile(window.innerWidth <= 760);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  useEffect(() => {
    document.body.classList.add('intro');
    const t = window.setTimeout(() => {
      document.body.classList.remove('intro');
      setIntroReady(true);
    }, reducedMotion ? 0 : 1600);
    return () => {
      window.clearTimeout(t);
      document.body.classList.remove('intro');
    };
  }, [reducedMotion]);

  useEffect(() => {
    const nodes = document.querySelectorAll<HTMLElement>('.reveal, .split');
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add('in');
          if (entry.target.classList.contains('split')) {
            entry.target.classList.remove('word-hidden');
            entry.target.classList.add('word-in');
          }
        });
      },
      { threshold: 0.2 },
    );
    nodes.forEach((n) => {
      if (n.classList.contains('split')) n.classList.add('word-hidden');
      io.observe(n);
    });
    const hero = document.getElementById('heroTitle');
    if (hero) {
      hero.classList.remove('word-hidden');
      hero.classList.add('word-in');
    }
    return () => io.disconnect();
  }, [introReady]);

  useEffect(() => {
    const el = statsRef.current;
    if (!el) return;
    const io = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) setCountersOn(true);
      },
      { threshold: 0.25 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  useEffect(() => {
    if (!countersOn) return;
    const start = performance.now();
    let frame = 0;
    const tick = (now: number): void => {
      const p = Math.min(1, (now - start) / 1800);
      setProgress(p);
      if (p < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [countersOn]);

  useEffect(() => {
    const el = footerRef.current;
    if (!el) return;
    const io = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) setFooterPlay(true);
      },
      { threshold: 0.4 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  const treeLift = countersOn ? (isMobile ? 0 : 6) : isMobile ? 40 : 75;

  return (
    <>
      {!introReady && (
        <div
          className="backdrop-hero"
          style={{ backgroundImage: `url(${HERO_POSTER})` }}
          aria-hidden="true"
        />
      )}
      <div id="landing-app">
        <section className="hero" id="hero">
          <nav className="nav" aria-label="Primary">
            <a className="brand" href="#hero" aria-label="Workload home">
              <BrandMark />
              <span>workload</span>
            </a>
            <Link className="btn" to={ctaHref}>
              {ctaLabel}
            </Link>
          </nav>

          <div className="cloud cloud-l">
            <img className="drift-a" src={CLOUD_A} alt="" />
          </div>
          <div className="cloud cloud-r">
            <img className="drift-b" src={CLOUD_B} alt="" />
          </div>

          <SplitHeadline as="h1" id="heroTitle" className="split">
            Balance the impact of
            <br />
            all your <em>faculty.</em>
          </SplitHeadline>

          <div className="hero-media">
            <video
              id="heroVideo"
              autoPlay
              muted
              loop
              playsInline
              preload="auto"
              poster={HERO_POSTER}
              src={HERO_VIDEO}
            />
          </div>

          <div className="hero-glass" aria-hidden="true">
            {GLASS_POS.map(([x, y], i) => {
              if (isMobile && i % 2 === 1) return null;
              const center = x > 40 && x < 60;
              return (
                <span
                  key={`${x}-${y}`}
                  className="glass"
                  style={{
                    left: `${x}%`,
                    top: `${y}%`,
                    width: center ? 'clamp(28px,3.4vw,44px)' : 'clamp(36px,5.4vw,74px)',
                    aspectRatio: '1',
                    animation: reducedMotion ? undefined : `glassFlicker 1.8s ease-in-out ${i * 0.12}s infinite alternate`,
                  }}
                />
              );
            })}
          </div>
        </section>

        <section className="stats" id="stats" ref={statsRef}>
          <div className="sq-field">
            {statsSquares.map((sq, i) => (
              <span
                key={`s-${i}`}
                className="grid-sq"
                style={{
                  left: sq.left,
                  top: sq.top,
                  animation: `sqPulse 2.4s ease-in-out ${sq.delay} infinite`,
                }}
              />
            ))}
          </div>
          <div className="tree-wrap">
            <img
              id="tree"
              className="tree"
              src={TREE}
              alt=""
              style={{
                transform: `translateY(${treeLift}%)`,
                transition: 'transform 1.4s cubic-bezier(0.22, 1, 0.36, 1)',
              }}
            />
          </div>
          <div className="stats-inner">
            <span className="pill reveal">
              {health?.status === 'healthy' ? 'Planner API online' : 'Teams rely on this cockpit'}
            </span>
            <SplitHeadline className="h2 split">
              Fair loads,
              <br />
              finished on constraints.
            </SplitHeadline>
            <div className="cards">
              {STAT_CARDS.map((card) => (
                <article className="card-ticket" key={card.label}>
                  <span>{card.label}</span>
                  <b>
                    {(card.to * progress).toFixed(card.dec)}
                    {card.suf}
                  </b>
                </article>
              ))}
            </div>
            <div className="cards-shadow" />
            <div className="logos-wrap">
              <div className="band" id="band" />
              <div className="logos">
                {ENGINE_MARKS.map((name) => (
                  <span className="logo-item" key={name}>
                    {name}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="loop" id="loop">
          <div className="loop-cloud">
            <img className="drift-a" src={CLOUD_A} alt="" />
            <span className="glass" style={{ left: '6%', top: '30%', width: '15%', aspectRatio: 1 }} />
            <span className="glass" style={{ left: '23%', top: '58%', width: '13%', aspectRatio: 1 }} />
            <span className="glass" style={{ left: '38%', top: '24%', width: '13%', aspectRatio: 1 }} />
          </div>
          <div className="loop-head">
            <span className="pill reveal">Human in the loop</span>
            <SplitHeadline className="h2 split">
              Chairs take over only at
              <br />
              the crunch.
            </SplitHeadline>
          </div>
          <div className="track" id="track">
            {LOOP_STEPS.map((step, index) => (
              <div
                key={step.num}
                className={`panel${activePanel === index ? ' is-active' : ''}`}
                tabIndex={0}
                aria-label={`Step ${step.num}: ${step.title}`}
                onMouseEnter={() => {
                  if (window.innerWidth >= 761) setActivePanel(index);
                }}
                onFocus={() => {
                  if (window.innerWidth >= 761) setActivePanel(index);
                }}
                onClick={() => {
                  if (window.innerWidth >= 761) setActivePanel(index);
                }}
              >
                <div className="panel-in">
                  <div className={`num num-${step.num}`}>{step.num}</div>
                  <div className="step">
                    <img className="mini-cloud" src={step.cloud} alt="" />
                    <h3>{step.title}</h3>
                    <p>{step.body}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="cta" id="cta">
          <div className="sq-field">
            {ctaSquares.map((sq, i) => (
              <span
                key={`c-${i}`}
                className="grid-sq"
                style={{
                  left: sq.left,
                  top: sq.top,
                  animation: `sqPulse 2.4s ease-in-out ${sq.delay} infinite`,
                }}
              />
            ))}
          </div>
          <div className="cta-img">
            <img id="ctaImg" alt="Moonlit cherry blossom valley" src={NIGHT} />
          </div>
          <div className="petals" id="petals" aria-hidden="true">
            {petals.map((p, i) => (
              <span
                key={i}
                className="petal"
                style={
                  {
                    left: p.left,
                    animationDuration: p.duration,
                    animationDelay: p.delay,
                    transform: `scale(${p.scale})`,
                    '--dx': p.dx,
                  } as React.CSSProperties
                }
              />
            ))}
          </div>
          <div className="cta-card" id="ctaCard">
            <span className="pill">Get started</span>
            <SplitHeadline className="h2 split">
              Every hour a fair assignment frees up is gold.
            </SplitHeadline>
            <p className="reveal">
              Sign in with a one-time passcode, run the solver, and see load, conflicts, and
              forecast bands on day one.
            </p>
            <Link className="btn reveal" to={ctaHref}>
              {ctaLabel}
            </Link>
          </div>
        </section>

        <footer className="site-footer" id="footer" ref={footerRef}>
          <svg className="f-logo" viewBox="0 0 80 80" overflow="visible" aria-label="Workload">
            <circle
              id="fRing"
              cx="40"
              cy="40"
              r="37"
              fill="none"
              stroke="#111"
              strokeWidth="2.4"
              strokeDasharray="233"
              strokeDashoffset={footerPlay ? 0 : 233}
              transform="rotate(-90 40 40)"
              style={{ transition: 'stroke-dashoffset 0.9s ease' }}
            />
            <circle className={`fdot${footerPlay ? ' play' : ''}`} cx="22" cy="40" r="4.5" fill="#111" />
            <circle className={`fdot${footerPlay ? ' play' : ''}`} cx="40" cy="40" r="4.5" fill="#111" />
            <circle className={`fdot${footerPlay ? ' play' : ''}`} cx="58" cy="40" r="4.5" fill="#111" />
            <path
              id="fMark"
              d="M33 53 43 31 56 53"
              fill="none"
              stroke="#111"
              strokeWidth="10"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeDasharray="60"
              strokeDashoffset={footerPlay ? 0 : 60}
              style={{ transition: 'stroke-dashoffset 0.6s ease 0.4s' }}
            />
          </svg>
          <nav className="f-links" aria-label="Footer">
            <Link to={isAuthenticated ? dashboardLink : '/login'}>Planner</Link>
            <a href="#loop">Mission</a>
            <Link to="/login">Help desk</Link>
            <a href="#stats">Terms</a>
          </nav>
          <div className="f-social" aria-label="Social">
            <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
              <path
                fill="#111"
                d="M18.244 2H21.5l-7.5 8.57L22.5 22h-6.56l-5.14-6.72L5.2 22H1.94l8.02-9.16L1.5 2h6.72l4.64 6.18L18.244 2Zm-1.15 18h1.8L7.02 3.92H5.1L17.094 20Z"
              />
            </svg>
            <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
              <rect x="3" y="3" width="18" height="18" rx="5" fill="none" stroke="#111" strokeWidth="1.7" />
              <circle cx="12" cy="12" r="4.2" fill="none" stroke="#111" strokeWidth="1.7" />
              <circle cx="17.4" cy="6.6" r="1.1" fill="#111" />
            </svg>
            <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
              <path
                fill="#111"
                d="M4.98 3.5A2.48 2.48 0 1 1 2.5 6a2.48 2.48 0 0 1 2.48-2.5ZM3 8.25h3.96V21H3V8.25ZM9.34 8.25H13.1v1.74h.05c.52-.98 1.8-2.02 3.71-2.02 3.97 0 4.7 2.61 4.7 6V21H17.6v-6.34c0-1.51-.03-3.46-2.11-3.46-2.11 0-2.43 1.65-2.43 3.35V21H9.34V8.25Z"
              />
            </svg>
          </div>
          <p className="f-copy">© 2026 Faculty Workload Balancing System. All rights reserved.</p>
        </footer>
      </div>
      <style>{`
        @keyframes glassFlicker {
          from { opacity: 1; }
          to { opacity: 0.15; }
        }
        @keyframes sqPulse {
          0%, 100% { opacity: 0.15; }
          50% { opacity: 1; }
        }
      `}</style>
    </>
  );
};
