import React from 'react';

function DatabaseViewer({ dbData, activeTab, onTabChange }) {
  const currentTableData = dbData[activeTab] || [];

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-white">
      
      {/* Database Tabs */}
      <div className="flex border-b border-gray-100 bg-white shrink-0">
        <button 
          onClick={() => onTabChange('orders')}
          className={`flex-1 py-3 text-xs font-medium border-b-2 transition duration-150 ${activeTab === 'orders' ? 'border-gray-900 text-gray-900 bg-gray-50/50' : 'border-transparent text-gray-400 hover:text-gray-650'}`}
        >
          <i className="fa-solid fa-truck-ramp-box mr-1.5"></i> Orders
        </button>
        <button 
          onClick={() => onTabChange('tickets')}
          className={`flex-1 py-3 text-xs font-medium border-b-2 transition duration-150 ${activeTab === 'tickets' ? 'border-gray-900 text-gray-900 bg-gray-50/50' : 'border-transparent text-gray-400 hover:text-gray-650'}`}
        >
          <i className="fa-solid fa-ticket mr-1.5"></i> Tickets
        </button>
        <button 
          onClick={() => onTabChange('accounts')}
          className={`flex-1 py-3 text-xs font-medium border-b-2 transition duration-150 ${activeTab === 'accounts' ? 'border-gray-900 text-gray-900 bg-gray-50/50' : 'border-transparent text-gray-400 hover:text-gray-650'}`}
        >
          <i className="fa-solid fa-circle-user mr-1.5"></i> Accounts
        </button>
      </div>

      {/* Dynamic Scoped Tables */}
      <div className="flex-1 overflow-auto p-4 bg-white">
        {currentTableData.length === 0 ? (
          <div className="p-8 text-center text-gray-400 border border-dashed border-gray-200 rounded-xl mt-4">
            No records found inside current security boundary.
          </div>
        ) : (
          <table className="w-full text-xs text-left text-gray-600">
            {activeTab === 'orders' && (
              <>
                <thead className="text-[10px] text-gray-400 uppercase bg-gray-50 border-b border-gray-100">
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
                <tbody className="divide-y divide-gray-100">
                  {currentTableData.map((item, idx) => {
                    const statusColor = item.status === 'DELIVERED' ? 'text-emerald-700 bg-emerald-50 border border-emerald-100' :
                                        item.status === 'CANCELLED' ? 'text-red-700 bg-red-50 border border-red-100' :
                                        'text-blue-700 bg-blue-50 border border-blue-100';
                    return (
                      <tr key={idx} className="hover:bg-gray-50/50 transition duration-150">
                        <td className="px-3 py-2.5 font-semibold text-gray-900">{item.order_id}</td>
                        <td className="px-3 py-2.5">{item.carrier}</td>
                        <td className="px-3 py-2.5"><span className={`px-2 py-0.5 rounded text-[10px] font-medium ${statusColor}`}>{item.status}</span></td>
                        <td className="px-3 py-2.5 text-gray-400">{item.booked_at}</td>
                        <td className="px-3 py-2.5 font-semibold text-gray-900">{item.shipment_fee_inr}</td>
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
                <thead className="text-[10px] text-gray-400 uppercase bg-gray-50 border-b border-gray-100">
                  <tr>
                    <th className="px-3 py-2.5">Ticket ID</th>
                    <th className="px-3 py-2.5">Status</th>
                    <th className="px-3 py-2.5">Subject</th>
                    <th className="px-3 py-2.5">Assigned To</th>
                    <th className="px-3 py-2.5">Channel</th>
                    <th className="px-3 py-2.5">Description</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {currentTableData.map((item, idx) => {
                    const statusColor = item.status === 'escalated' ? 'text-amber-700 bg-amber-50 border border-amber-100' :
                                        item.status === 'open' ? 'text-blue-700 bg-blue-50 border border-blue-100' :
                                        'text-gray-500 bg-gray-50 border border-gray-100';
                    return (
                      <tr key={idx} className="hover:bg-gray-50/50 transition duration-150">
                        <td className="px-3 py-2.5 font-semibold text-gray-900">{item.ticket_id}</td>
                        <td className="px-3 py-2.5"><span className={`px-2 py-0.5 rounded text-[10px] font-medium ${statusColor}`}>{item.status}</span></td>
                        <td className="px-3 py-2.5 font-medium text-gray-800">{item.subject}</td>
                        <td className="px-3 py-2.5 text-gray-600">{item.assigned_to}</td>
                        <td className="px-3 py-2.5 uppercase text-[10px] text-gray-400 font-semibold">{item.channel}</td>
                        <td className="px-3 py-2.5 text-gray-400 max-w-[200px] truncate" title={item.description}>{item.description || '-'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </>
            )}

            {activeTab === 'accounts' && (
              <>
                <thead className="text-[10px] text-gray-400 uppercase bg-gray-50 border-b border-gray-100">
                  <tr>
                    <th className="px-3 py-2.5">Account ID</th>
                    <th className="px-3 py-2.5">Name</th>
                    <th className="px-3 py-2.5">Plan</th>
                    <th className="px-3 py-2.5">CSM</th>
                    <th className="px-3 py-2.5">Premium</th>
                    <th className="px-3 py-2.5">Notes</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {currentTableData.map((item, idx) => (
                    <tr key={idx} className="hover:bg-gray-50/50 transition duration-150">
                      <td className="px-3 py-2.5 font-semibold text-gray-900">{item.account_id}</td>
                      <td className="px-3 py-2.5 font-medium text-gray-800">{item.account_name}</td>
                      <td className="px-3 py-2.5 text-gray-600">{item.plan}</td>
                      <td className="px-3 py-2.5 text-gray-600">{item.csm}</td>
                      <td className="px-3 py-2.5">
                        <span className={item.premium_support ? 'text-emerald-600 font-semibold' : 'text-gray-400'}>
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
