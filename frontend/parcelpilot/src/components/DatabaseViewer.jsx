import React from 'react';

function DatabaseViewer({ dbData, activeTab, onTabChange }) {
  const currentTableData = dbData[activeTab] || [];

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-[#070b13]/10">
      
      {/* Database Tabs */}
      <div className="flex border-b border-gray-800 bg-[#070b13]/30 shrink-0">
        <button 
          onClick={() => onTabChange('orders')}
          className={`flex-1 py-3 text-xs font-semibold border-b-2 transition duration-150 ${activeTab === 'orders' ? 'border-blue-500 text-blue-400 bg-gray-900/10' : 'border-transparent text-gray-400 hover:text-gray-200'}`}
        >
          <i className="fa-solid fa-truck-ramp-box mr-1.5"></i> Orders
        </button>
        <button 
          onClick={() => onTabChange('tickets')}
          className={`flex-1 py-3 text-xs font-semibold border-b-2 transition duration-150 ${activeTab === 'tickets' ? 'border-blue-500 text-blue-400 bg-gray-900/10' : 'border-transparent text-gray-400 hover:text-gray-200'}`}
        >
          <i className="fa-solid fa-ticket mr-1.5"></i> Tickets
        </button>
        <button 
          onClick={() => onTabChange('accounts')}
          className={`flex-1 py-3 text-xs font-semibold border-b-2 transition duration-150 ${activeTab === 'accounts' ? 'border-blue-500 text-blue-400 bg-gray-900/10' : 'border-transparent text-gray-400 hover:text-gray-200'}`}
        >
          <i className="fa-solid fa-circle-user mr-1.5"></i> Accounts
        </button>
      </div>

      {/* Dynamic Scoped Tables */}
      <div className="flex-1 overflow-auto p-4">
        {currentTableData.length === 0 ? (
          <div className="p-8 text-center text-gray-600 border border-dashed border-gray-800 rounded-xl mt-4">
            No records found inside current security boundary.
          </div>
        ) : (
          <table className="w-full text-xs text-left text-gray-300">
            {activeTab === 'orders' && (
              <>
                <thead className="text-[10px] text-gray-400 uppercase bg-gray-950/70 border-b border-gray-800">
                  <tr>
                    <th className="px-3 py-2.5">Order ID</th>
                    <th className="px-3 py-2.5">Carrier</th>
                    <th className="px-3 py-2.5">Status</th>
                    <th className="px-3 py-2.5">Booked At</th>
                    <th className="px-3 py-2.5">Fee (INR)</th>
                    <th className="px-3 py-2.5">Fault</th>
                    <th className="px-3 py-2.5">Notes</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800/60">
                  {currentTableData.map((item, idx) => {
                    const statusColor = item.status === 'DELIVERED' ? 'text-emerald-400 bg-emerald-500/10 border border-emerald-500/20' :
                                        item.status === 'CANCELLED' ? 'text-red-400 bg-red-500/10 border border-red-500/20' :
                                        'text-blue-400 bg-blue-500/10 border border-blue-500/20';
                    return (
                      <tr key={idx} className="hover:bg-gray-900/25 transition duration-150">
                        <td className="px-3 py-2.5 font-semibold text-gray-100">{item.order_id}</td>
                        <td className="px-3 py-2.5">{item.carrier}</td>
                        <td className="px-3 py-2.5"><span className={`px-2 py-0.5 rounded text-[10px] ${statusColor}`}>{item.status}</span></td>
                        <td className="px-3 py-2.5 text-gray-400">{item.booked_at}</td>
                        <td className="px-3 py-2.5 font-bold text-gray-100">{item.shipment_fee_inr}</td>
                        <td className="px-3 py-2.5 text-gray-400">
                          {item.carrier_fault ? 'Carrier' : ''}
                          {item.customer_fault ? 'Customer' : ''}
                          {(!item.carrier_fault && !item.customer_fault) ? 'None' : ''}
                        </td>
                        <td className="px-3 py-2.5 text-gray-400 max-w-[150px] truncate" title={item.notes}>{item.notes || '-'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </>
            )}

            {activeTab === 'tickets' && (
              <>
                <thead className="text-[10px] text-gray-400 uppercase bg-gray-950/70 border-b border-gray-800">
                  <tr>
                    <th className="px-3 py-2.5">Ticket ID</th>
                    <th className="px-3 py-2.5">Status</th>
                    <th className="px-3 py-2.5">Subject</th>
                    <th className="px-3 py-2.5">Assigned To</th>
                    <th className="px-3 py-2.5">Channel</th>
                    <th className="px-3 py-2.5">Description</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800/60">
                  {currentTableData.map((item, idx) => {
                    const statusColor = item.status === 'escalated' ? 'text-amber-400 bg-amber-500/10 border border-amber-500/20' :
                                        item.status === 'open' ? 'text-blue-400 bg-blue-500/10 border border-blue-500/20' :
                                        'text-gray-400 bg-gray-800/25';
                    return (
                      <tr key={idx} className="hover:bg-gray-900/25 transition duration-150">
                        <td className="px-3 py-2.5 font-semibold text-gray-100">{item.ticket_id}</td>
                        <td className="px-3 py-2.5"><span className={`px-2 py-0.5 rounded text-[10px] ${statusColor}`}>{item.status}</span></td>
                        <td className="px-3 py-2.5 font-medium text-gray-200">{item.subject}</td>
                        <td className="px-3 py-2.5 text-gray-300">{item.assigned_to}</td>
                        <td className="px-3 py-2.5 uppercase text-[10px] text-gray-500 font-semibold">{item.channel}</td>
                        <td className="px-3 py-2.5 text-gray-400 max-w-[200px] truncate" title={item.description}>{item.description || '-'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </>
            )}

            {activeTab === 'accounts' && (
              <>
                <thead className="text-[10px] text-gray-400 uppercase bg-gray-950/70 border-b border-gray-800">
                  <tr>
                    <th className="px-3 py-2.5">Account ID</th>
                    <th className="px-3 py-2.5">Name</th>
                    <th className="px-3 py-2.5">Plan</th>
                    <th className="px-3 py-2.5">CSM</th>
                    <th className="px-3 py-2.5">Premium</th>
                    <th className="px-3 py-2.5">Notes</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800/60">
                  {currentTableData.map((item, idx) => (
                    <tr key={idx} className="hover:bg-gray-900/25 transition duration-150">
                      <td className="px-3 py-2.5 font-semibold text-gray-100">{item.account_id}</td>
                      <td className="px-3 py-2.5 font-medium text-gray-200">{item.account_name}</td>
                      <td className="px-3 py-2.5">{item.plan}</td>
                      <td className="px-3 py-2.5">{item.csm}</td>
                      <td className="px-3 py-2.5">
                        <span className={item.premium_support ? 'text-emerald-400 font-semibold' : 'text-gray-500'}>
                          {item.premium_support ? 'YES' : 'NO'}
                        </span>
                      </td>
                      <td className="px-3 py-2.5 text-gray-400 max-w-[150px] truncate" title={item.notes}>{item.notes || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </>
            )}
          </table>
        )}
      </div>

    </div>
  );
}

export default DatabaseViewer;
