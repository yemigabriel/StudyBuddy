export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-4xl flex-col gap-6 px-6 py-12">
      <section className="rounded-xl bg-white p-6 shadow-sm">
        <h1 className="text-3xl font-semibold">StudyBuddy</h1>
        <p className="mt-2 text-slate-600">
          Upload study material and chat with your notes.
        </p>
      </section>

      <section className="rounded-xl bg-white p-6 shadow-sm">
        <h2 className="text-xl font-medium">Upload</h2>
        <input
          className="mt-4 block w-full rounded-md border border-slate-300 p-3"
          type="file"
        />
      </section>

      <section className="rounded-xl bg-white p-6 shadow-sm">
        <h2 className="text-xl font-medium">Chat</h2>
        <div className="mt-4 min-h-48 rounded-md border border-dashed border-slate-300 p-4 text-slate-500">
          Responses will appear here.
        </div>
        <div className="mt-4 flex gap-3">
          <input
            className="flex-1 rounded-md border border-slate-300 p-3"
            placeholder="Ask a question about your material..."
            type="text"
          />
          <button className="rounded-md bg-slate-900 px-5 py-3 text-white">
            Send
          </button>
        </div>
      </section>
    </main>
  );
}
