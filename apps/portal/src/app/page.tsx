'use client'

import { useEffect, useState } from 'react'

interface Ticket {
  id: string
  ticket_number: string
  status: string
  priority: string
  trade: string | null
  summary: string
  created_at: string
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const STATUS_COLORS: Record<string, string> = {
  new: 'bg-blue-100 text-blue-800',
  qualifying: 'bg-yellow-100 text-yellow-800',
  dispatching: 'bg-orange-100 text-orange-800',
  quotes_pending: 'bg-purple-100 text-purple-800',
  awaiting_approval: 'bg-red-100 text-red-800',
  scheduled: 'bg-indigo-100 text-indigo-800',
  in_progress: 'bg-cyan-100 text-cyan-800',
  awaiting_invoice: 'bg-amber-100 text-amber-800',
  awaiting_payment: 'bg-pink-100 text-pink-800',
  closed: 'bg-green-100 text-green-800',
}

const PRIORITY_COLORS: Record<string, string> = {
  emergency: 'bg-red-600 text-white',
  urgent: 'bg-orange-500 text-white',
  routine: 'bg-gray-200 text-gray-700',
}

export default function Dashboard() {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('all')

  useEffect(() => {
    fetchTickets()
  }, [filter])

  async function fetchTickets() {
    try {
      const params = filter !== 'all' ? `?status=${filter}` : ''
      const res = await fetch(`${API_BASE}/tickets${params}`)
      if (res.ok) {
        const data = await res.json()
        setTickets(data)
      }
    } catch (err) {
      console.error('Failed to fetch tickets:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-xl font-bold">Agentic PM - Maintenance Desk</h1>
          <div className="flex gap-2">
            <span className="text-sm text-gray-500">
              {tickets.length} ticket{tickets.length !== 1 ? 's' : ''}
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Filter Bar */}
        <div className="flex gap-2 mb-6 flex-wrap">
          {['all', 'new', 'qualifying', 'dispatching', 'quotes_pending',
            'awaiting_approval', 'scheduled', 'in_progress', 'closed'].map((s) => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`px-3 py-1 rounded-full text-sm ${
                filter === s
                  ? 'bg-gray-900 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {s.replace(/_/g, ' ')}
            </button>
          ))}
        </div>

        {/* Ticket List */}
        {loading ? (
          <div className="text-center py-12 text-gray-400">Loading tickets...</div>
        ) : tickets.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            No tickets found. Tickets will appear here when tenants submit maintenance requests.
          </div>
        ) : (
          <div className="space-y-3">
            {tickets.map((ticket) => (
              <div
                key={ticket.id}
                className="bg-white rounded-lg shadow-sm border p-4 hover:shadow-md transition-shadow cursor-pointer"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono text-sm text-gray-500">
                        {ticket.ticket_number}
                      </span>
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          STATUS_COLORS[ticket.status] || 'bg-gray-100'
                        }`}
                      >
                        {ticket.status.replace(/_/g, ' ')}
                      </span>
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          PRIORITY_COLORS[ticket.priority] || ''
                        }`}
                      >
                        {ticket.priority}
                      </span>
                      {ticket.trade && (
                        <span className="px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-600">
                          {ticket.trade}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-800">{ticket.summary}</p>
                  </div>
                  <div className="text-xs text-gray-400 ml-4 whitespace-nowrap">
                    {new Date(ticket.created_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
