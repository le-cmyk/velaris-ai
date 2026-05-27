import { Bot, User2 } from 'lucide-react';

import { ExecutionTimeline } from '@/components/chat/ExecutionTimeline';
import { ToolCallCard } from '@/components/chat/ToolCallCard';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import type { Message } from '@/types';

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-3xl ${isUser ? 'items-end' : 'items-start'} flex w-full flex-col gap-3`}>
        <div
          className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium ${
            isUser ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-700'
          }`}
        >
          {isUser ? <User2 className="h-3.5 w-3.5" /> : <Bot className="h-3.5 w-3.5" />}
          {isUser ? 'You' : 'Velaris Agent'} · {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>

        <Card className={`w-full ${isUser ? 'border-blue-200 bg-blue-50' : 'bg-white'}`}>
          <CardContent className="space-y-5 p-5">
            <p className="whitespace-pre-wrap text-sm leading-6 text-slate-800">{message.content}</p>

            {message.chatResponse ? (
              <div className="space-y-5 rounded-xl border border-slate-200 bg-slate-50 p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="secondary">Intent: {message.chatResponse.intent}</Badge>
                  <Badge variant={message.chatResponse.pending_approvals.length > 0 ? 'warning' : 'success'}>
                    {message.chatResponse.status}
                  </Badge>
                  {message.chatResponse.pending_approvals.length > 0 ? (
                    <Badge variant="warning">{message.chatResponse.pending_approvals.length} approvals pending</Badge>
                  ) : null}
                </div>

                <ExecutionTimeline
                  intent={message.chatResponse.intent}
                  executionPlan={message.chatResponse.execution_plan}
                  toolCallsCount={message.chatResponse.tool_calls.length}
                />

                {message.chatResponse.tool_calls.length > 0 ? (
                  <div className="space-y-3">
                    <h4 className="text-sm font-semibold text-slate-900">Tool calls</h4>
                    <div className="space-y-3">
                      {message.chatResponse.tool_calls.map((toolCall, index) => (
                        <ToolCallCard key={`${toolCall.tool_name}-${index}`} toolCall={toolCall} />
                      ))}
                    </div>
                  </div>
                ) : null}
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
