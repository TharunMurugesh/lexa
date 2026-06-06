import { useEffect, useState } from 'react'
import { AgentPanel } from '../components/AgentPanel'
import { CaseHistory } from '../components/CaseHistory'
import { CaseUploader } from '../components/CaseUploader'
import { VerdictCard } from '../components/VerdictCard'
import { getCases, getLogs, getVerdict, type AgentLog, type CaseSummary, type Verdict } from '../lib/api'
import { supabase } from '../lib/supabase'

export function Home() {
  const [caseId, setCaseId] = useState('')
  const [logs, setLogs] = useState<AgentLog[]>([])
  const [verdict, setVerdict] = useState<Verdict | null>(null)
  const [cases, setCases] = useState<CaseSummary[]>([])

  async function refresh(id = caseId) {
    const caseList = await getCases()
    setCases(caseList)
    if (!id) return
    setLogs(await getLogs(id))
    const verdictResponse = await getVerdict(id)
    setVerdict(verdictResponse?.verdict === null ? null : verdictResponse)
  }

  useEffect(() => {
    refresh().catch(console.error)
  }, [])

  useEffect(() => {
    if (!caseId) return
    refresh(caseId).catch(console.error)
    const timer = window.setInterval(() => refresh(caseId).catch(console.error), 1200)
    return () => window.clearInterval(timer)
  }, [caseId])

  useEffect(() => {
    if (!caseId || !supabase) return
    const client = supabase
    const channel = client
      .channel('agent-progress')
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'agent_logs', filter: `case_id=eq.${caseId}` },
        (payload) => setLogs((current) => [...current, payload.new as AgentLog]),
      )
      .subscribe()
    return () => {
      client.removeChannel(channel)
    }
  }, [caseId])

  function selectCase(id: string) {
    setCaseId(id)
    setVerdict(null)
    setLogs([])
  }

  return (
    <main>
      <header className="topbar">
        <div>
          <h1>LEXA</h1>
          <p>Autonomous multi-agent courtroom intelligence for Indian legal case analysis.</p>
        </div>
        <span className="status-pill">FastAPI + LangGraph + NIM</span>
      </header>
      <div className="workspace">
        <aside>
          <CaseUploader onCaseCreated={selectCase} />
          <CaseHistory cases={cases} activeCaseId={caseId} onSelect={selectCase} />
        </aside>
        <div className="main-stack">
          <AgentPanel logs={logs} />
          <VerdictCard verdict={verdict} />
        </div>
      </div>
    </main>
  )
}
