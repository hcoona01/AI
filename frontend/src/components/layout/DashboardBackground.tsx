import React, { useMemo } from 'react';
import { HERO_POSTER, HERO_VIDEO, CLOUD_A, CLOUD_B } from '../../lib/visualAssets';

interface PetalSpec {
  left: string;
  dx: string;
  duration: string;
  delay: string;
  scale: number;
}

export const DashboardBackground: React.FC = () => {
  const petals: PetalSpec[] = useMemo(
    () =>
      Array.from({ length: 14 }, () => ({
        left: `${Math.random() * 100}%`,
        dx: `${Math.round(Math.random() * 140 - 70)}px`,
        duration: `${10 + Math.random() * 8}s`,
        delay: `${-Math.random() * 12}s`,
        scale: 0.6 + Math.random() * 0.6,
      })),
    []
  );

  return (
    <div className="dashboard-bg-fixed" aria-hidden="true">
      {/* High-definition Cherry Blossom Valley Poster Image */}
      <img className="dashboard-bg-poster" src={HERO_POSTER} alt="" />

      {/* Looping Scene Video with petals/river/birds */}
      <video
        className="dashboard-bg-video"
        autoPlay
        muted
        loop
        playsInline
        poster={HERO_POSTER}
      >
        <source src={HERO_VIDEO} type="video/mp4" />
      </video>

      {/* Floating anime clouds */}
      <img className="dashboard-bg-cloud dashboard-bg-cloud--left drift-a" src={CLOUD_A} alt="" />
      <img className="dashboard-bg-cloud dashboard-bg-cloud--right drift-b" src={CLOUD_B} alt="" />

      {/* Falling Cherry Blossom Petals */}
      <div className="petals pointer-events-none">
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

      {/* Delicate translucent veil ensuring high UI contrast and readability */}
      <div className="dashboard-bg-veil" />
    </div>
  );
};
