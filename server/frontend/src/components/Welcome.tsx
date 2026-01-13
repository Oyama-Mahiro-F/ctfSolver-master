import { useNavigate } from 'react-router-dom';
import { GlassButton, GlassFilter } from '@/components/ui/liquid-glass';
import { AuroraBackground } from '@/components/ui/aurora-background';
import { AnimatedText } from '@/components/ui/animated-underline-text-one';

export function Welcome() {
  const navigate = useNavigate();

  return (
    <AuroraBackground className="min-h-screen">
      <GlassFilter />
      <div className="min-h-screen flex items-center justify-center relative z-10">
        <div className="flex flex-col gap-8 items-center justify-center max-w-2xl mx-auto px-4">
          <div className="text-center space-y-4">
            <AnimatedText
              text="CTF Solver"
              textClassName="text-6xl font-bold text-zinc-900 dark:text-white mb-4"
              underlineClassName="text-zinc-900 dark:text-white"
              underlinePath="M 0,10 Q 100,0 200,10 Q 300,20 400,10"
              underlineHoverPath="M 0,10 Q 100,20 200,10 Q 300,0 400,10"
              underlineDuration={1.5}
            />
            <p className="text-xl text-zinc-700 dark:text-zinc-300 mt-8">
              智能渗透测试与漏洞挖掘平台
            </p>
            <p className="text-lg text-zinc-600 dark:text-zinc-400">
              自动化任务管理 · 漏洞发现 · Agent 协作
            </p>
          </div>

          <div className="flex flex-col gap-4 w-full max-w-xs">
            <GlassButton onClick={() => navigate('/home')} className="w-full !px-6 !py-3">
              <div className="text-sm text-zinc-900 dark:text-white text-center font-semibold">
                开始使用
              </div>
            </GlassButton>
          </div>
        </div>
      </div>
    </AuroraBackground>
  );
}
