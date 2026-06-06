import { useState } from 'react'
import { createTextCase, uploadCase } from '../lib/api'

const sampleText =
  'The complaint states that Rohan argued with the victim outside a shop at 8:30 PM. A witness says Rohan struck the victim with a metal rod. The victim later died in hospital. The defense says the witness was standing far away and could not clearly identify the attacker. Police recovered a rod, but the forensic report is inconclusive.'

type Props = {
  onCaseCreated: (caseId: string) => void
}

export function CaseUploader({ onCaseCreated }: Props) {
  const [title, setTitle] = useState('Sample Case: State v. Rohan')
  const [text, setText] = useState(sampleText)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')

  async function submitText() {
    setBusy(true)
    setMessage('')
    try {
      const result = await createTextCase(title, text)
      onCaseCreated(result.case_id)
      setMessage('Case submitted. Agents are analyzing it now.')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Could not submit case')
    } finally {
      setBusy(false)
    }
  }

  async function submitFile(file: File | null) {
    if (!file) return
    setBusy(true)
    setMessage('')
    try {
      const result = await uploadCase(file)
      onCaseCreated(result.case_id)
      setMessage('Document uploaded. Agents are analyzing it now.')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Could not upload document')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="upload-panel">
      <div className="section-heading">
        <span>Case intake</span>
        <strong>Upload PDF/TXT or run the bundled sample</strong>
      </div>
      <label>
        <span>Case title</span>
        <input value={title} onChange={(event) => setTitle(event.target.value)} />
      </label>
      <label>
        <span>Case text</span>
        <textarea value={text} onChange={(event) => setText(event.target.value)} rows={8} />
      </label>
      <div className="actions">
        <button onClick={submitText} disabled={busy || !text.trim()}>
          {busy ? 'Analyzing...' : 'Analyze Text'}
        </button>
        <label className="file-button">
          Upload File
          <input
            type="file"
            accept=".pdf,.txt"
            onChange={(event) => submitFile(event.target.files?.[0] ?? null)}
            disabled={busy}
          />
        </label>
      </div>
      {message && <p className="notice">{message}</p>}
    </section>
  )
}
