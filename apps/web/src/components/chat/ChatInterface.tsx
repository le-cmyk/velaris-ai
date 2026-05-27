'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { Loader2, Send, Sparkles } from 'lucide-react';

import { MessageBubble } from '@/components/chat/MessageBubble';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { api } from '@/lib/api';
import { getUser } from '@/lib/auth';
import type { Message } from '@/types';

const exampleQueries = [
  'Show me the list of customers',
  'Summarize pending approvals for today',
  'Check the status of the reporting workflow',
];

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  const workspaceId = useMemo(() => getUser()?.workspace_id ?? 'default-workspace', []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = async (rawMessage?: string) => {
    const content = (rawMessage ?? input).trim();
    if (!content || loading) return;

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages((current) => [...current, userMessage]);
    setInput('');
    setLoading(true);
    setError(null);

    try {
      const response = await api.sendMessage(content, workspaceId);
      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: response.message,
        timestamp: new Date(),
        chatResponse: response,
      };
      setMessages((current) => [...current, assistantMessage]);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unable to reach the Velaris API.';
      setError(message);
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: `I ran into an error while processing that request: ${message}`,
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-full min-h-[70vh] flex-col gap-4">
      <Card className="flex-1 overflow-hidden border-slate-200">
        <CardContent className="flex h-full flex-col gap-6 p-6">
          {messages.length === 0 ? (
            <div className="flex flex-1 flex-col items-center justify-center gap-6 text-center">
              <div className="rounded-full bg-blue-100 p-3 text-blue-700">
                <Sparkles className="h-6 w-6" />
              </div>
              <div className="space-y-2">
                <h2 className="text-2xl font-semibold text-slate-950">Start a new agent run</h2>
                <p className="max-w-xl text-sm text-slate-500">
                  Ask Velaris AI to inspect systems, orchestrate workflows, or gather enterprise context across your tools.
                </p>
              </div>
              <div className="flex flex-wrap justify-center gap-3">
                {exampleQueries.map((query) => (
                  <Button key={query} variant="outline" onClick={() => handleSend(query)}>
                    {query}
                  </Button>
                ))}
              </div>
            </div>
          ) : (
            <div className="flex-1 space-y-6 overflow-y-auto pr-1">
              {messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))}
              {loading ? (
                <div className="flex items-center gap-2 text-sm text-slate-500">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Velaris is reasoning through your request...
                </div>
              ) : null}
              <div ref={bottomRef} />
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="border-slate-200">
        <CardContent className="space-y-3 p-4">
          {error ? <p className="text-sm text-red-600">{error}</p> : null}
          <div className="flex flex-col gap-3 sm:flex-row">
            <Input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault();
                  void handleSend();
                }
              }}
              placeholder="Ask Velaris AI to analyze a workflow, inspect tools, or summarize operations..."
              className="min-h-10 flex-1"
            />
            <Button onClick={() => void handleSend()} disabled={loading || input.trim().length === 0} className="gap-2">
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              Send message
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
