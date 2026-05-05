import { FormEvent, useState } from 'react';
import { MessageSquare, X } from 'lucide-react';
import { api } from '../lib/api';

export function FeedbackButton() {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState('');

  async function submit(event: FormEvent) {
    event.preventDefault();
    setStatus('Sending...');
    try {
      await api.post('/api/feedback', {
        message,
        email: email || undefined,
        page: window.location.pathname,
      });
      setMessage('');
      setEmail('');
      setStatus('Thanks for the feedback.');
    } catch {
      setStatus('Feedback could not be sent.');
    }
  }

  if (!open) {
    return (
      <button
        type="button"
        aria-label="Feedback"
        title="Feedback"
        onClick={() => setOpen(true)}
        className="fixed bottom-5 right-5 z-40 inline-flex h-12 w-12 items-center justify-center rounded-full border border-grunge-acid/40 bg-grunge-acid text-grunge-black shadow-neon-acid transition hover:brightness-110"
      >
        <MessageSquare className="h-5 w-5" />
      </button>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-end bg-black/40 p-4 backdrop-blur-sm md:p-6">
      <form
        onSubmit={submit}
        className="w-full max-w-sm rounded-lg border border-grunge-charcoal bg-grunge-black p-4 shadow-2xl"
      >
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-display text-lg font-bold text-grunge-acid">Feedback</h2>
          <button
            type="button"
            aria-label="Close feedback"
            title="Close"
            onClick={() => setOpen(false)}
            className="inline-flex h-8 w-8 items-center justify-center rounded-md text-gray-400 transition hover:bg-grunge-charcoal hover:text-white"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <textarea
          aria-label="Feedback"
          required
          rows={5}
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          className="mb-3 w-full rounded-md border border-grunge-charcoal bg-black/40 px-3 py-2 text-sm text-white outline-none transition placeholder:text-gray-500 focus:border-grunge-acid"
          placeholder="What should we fix or add?"
        />
        <input
          aria-label="Email"
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className="mb-3 w-full rounded-md border border-grunge-charcoal bg-black/40 px-3 py-2 text-sm text-white outline-none transition placeholder:text-gray-500 focus:border-grunge-acid"
          placeholder="Email, optional"
        />
        <button
          type="submit"
          className="w-full rounded-md bg-grunge-acid px-4 py-2 text-sm font-bold text-grunge-black transition hover:brightness-110"
        >
          Send
        </button>
        {status ? <p className="mt-3 text-sm text-gray-300">{status}</p> : null}
      </form>
    </div>
  );
}
