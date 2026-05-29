'use client';

import { useEffect, useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Loader2, LockKeyhole, Mail } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { ApiDebugPanel } from '@/components/debug/ApiDebugPanel';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { api } from '@/lib/api';
import { isAuthenticated, saveToken, saveUser } from '@/lib/auth';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('demo@velaris.ai');
  const [password, setPassword] = useState('demo123');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated()) {
      router.replace('/dashboard');
    }
  }, [router]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const { token, user } = await api.login(email, password);
      saveToken(token);
      saveUser(user);
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to sign in.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen bg-slate-950">
      <section className="hidden flex-1 flex-col justify-between bg-[radial-gradient(circle_at_top_left,_rgba(96,165,250,0.35),_transparent_35%),linear-gradient(135deg,#020617_0%,#0f172a_55%,#1e293b_100%)] p-12 text-white lg:flex">
        <div className="flex items-center gap-4">
          <Image src="/logo.svg" alt="Velaris AI" width={52} height={52} priority />
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-blue-200">Velaris AI</p>
            <h1 className="text-3xl font-semibold">Agentic operations for modern teams</h1>
          </div>
        </div>

        <div className="max-w-xl space-y-6">
          <h2 className="text-5xl font-semibold leading-tight">Secure multi-agent workflows, approvals, and observability in one console.</h2>
          <p className="text-lg text-slate-300">
            Connect enterprise systems, coordinate tool execution, and keep human approvals in the loop with an interface built for production operations.
          </p>
        </div>

        <div className="grid grid-cols-3 gap-4 text-sm text-slate-300">
          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <p className="text-2xl font-semibold text-white">12</p>
            <p>Connected tools</p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <p className="text-2xl font-semibold text-white">28</p>
            <p>Runs executed today</p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <p className="text-2xl font-semibold text-white">100%</p>
            <p>Audit coverage</p>
          </div>
        </div>
      </section>

      <section className="flex flex-1 items-center justify-center p-6 sm:p-10">
        <div className="w-full max-w-md space-y-4">
          <Card className="border-slate-200 shadow-xl shadow-slate-200/60">
            <CardHeader className="space-y-2 text-center">
              <div className="mx-auto rounded-full bg-blue-100 p-3 text-blue-600">
                <LockKeyhole className="h-6 w-6" />
              </div>
              <CardTitle className="text-3xl">Welcome back</CardTitle>
              <CardDescription>Use the demo workspace credentials to access the Velaris control plane.</CardDescription>
            </CardHeader>
            <CardContent>
              <form className="space-y-5" onSubmit={handleSubmit}>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <div className="relative">
                    <Mail className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-400" />
                    <Input id="email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} className="pl-9" />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                  />
                </div>
                {error ? <p className="text-sm text-red-600">{error}</p> : null}
                <Button type="submit" className="w-full" disabled={loading}>
                  {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                  Sign in to workspace
                </Button>
                <div className="space-y-2 text-center text-sm text-slate-500">
                  <p>
                    Don&apos;t have an account?{' '}
                    <Link href="/signup" className="font-medium text-blue-600 hover:underline">
                      Create one
                    </Link>
                  </p>
                  <p>
                    API connectivity issue?{' '}
                    <Link href="/debug-api" className="font-medium text-blue-600 hover:underline">
                      Open /debug-api
                    </Link>
                  </p>
                </div>
              </form>
            </CardContent>
          </Card>

          <ApiDebugPanel compact />
        </div>
      </section>
    </main>
  );
}
