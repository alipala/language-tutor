'use client';

import VerticalCarouselFlow from '@/components/vertical-carousel-flow';
import NavBar from '@/components/nav-bar';
import '@/styles/carousel-animations.css';

export default function FlowPage() {
  return (
    <div className="min-h-screen overflow-x-hidden w-full">
      <NavBar />
      <VerticalCarouselFlow />
    </div>
  );
}
