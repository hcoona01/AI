import React from 'react';
import { CLOUD_A, CLOUD_B, HERO_POSTER, HERO_VIDEO } from '../../lib/visualAssets';

/**
 * A deliberately quiet version of the landing scene for authenticated screens.
 * It is purely decorative and kept outside the document flow so dashboard
 * controls retain their normal layout and interaction behaviour.
 */
export const DashboardAtmosphere: React.FC = () => (
  <div className="dashboard-atmosphere" aria-hidden="true">
    <video
      className="dashboard-atmosphere__video"
      autoPlay
      loop
      muted
      playsInline
      poster={HERO_POSTER}
    >
      <source src={HERO_VIDEO} type="video/mp4" />
    </video>
    <img className="dashboard-atmosphere__cloud dashboard-atmosphere__cloud--left drift-a" src={CLOUD_A} alt="" />
    <img className="dashboard-atmosphere__cloud dashboard-atmosphere__cloud--right drift-b" src={CLOUD_B} alt="" />
    <div className="dashboard-atmosphere__wash" />
  </div>
);
