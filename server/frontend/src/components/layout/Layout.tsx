import { ReactNode } from 'react';
import { TopNav } from './TopNav';
import { AuroraBackground } from '@/components/ui/aurora-background';
import { GlassFilter } from '@/components/ui/liquid-glass';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <>
      <GlassFilter />
      <TopNav />
      <AuroraBackground className="min-h-screen pt-12">
        <div className="container mx-auto px-4 pt-4 pb-8">
          {children}
        </div>
      </AuroraBackground>
    </>
  );
}
