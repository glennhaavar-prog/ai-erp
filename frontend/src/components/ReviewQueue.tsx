'use client';

import React, { useState, useEffect } from 'react';
import { ReviewItem, ReviewStatus, Priority, ChatMessage } from '@/types/review-queue';
import { ReviewQueueItem } from './ReviewQueueItem';
import { InvoiceDetails } from './InvoiceDetails';
import { BookingDetails } from './BookingDetails';
import { FilterBar } from './FilterBar';
import { ApproveButton } from './ApproveButton';
import { CorrectButton } from './CorrectButton';
import { ChatInterface } from './ChatInterface';
import { PatternList } from './PatternList';
import { reviewQueueApi } from '@/api/review-queue';
import { toast } from '@/lib/toast';
import { useClient } from '@/contexts/ClientContext';

export const ReviewQueue: React.FC = () => {
  const { selectedClient, isLoading: clientLoading } = useClient();
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedItem, setSelectedItem] = useState<ReviewItem | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<ReviewStatus | undefined>();
  const [selectedPriority, setSelectedPriority] = useState<Priority | undefined>();
  const [searchQuery, setSearchQuery] = useState('');
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [activeTab, setActiveTab] = useState<'details' | 'chat' | 'patterns'>('details');

  // Fetch items from API when client is selected
  useEffect(() => {
    if (!selectedClient?.id) {
      setItems([]);
      setLoading(false);
      return;
    }

    const fetchItems = async () => {
      try {
        setLoading(true);
        const data = await reviewQueueApi.getReviewItems({ client_id: selectedClient.id });
        // Backend returns {items: [], total, page, page_size}
        const itemsArray = Array.isArray(data) ? data : ((data as any).items || []);
        setItems(itemsArray);
        if (itemsArray.length > 0 && !selectedItem) {
          setSelectedItem(itemsArray[0]);
        }
        setError(null);
      } catch (err) {
        console.error('Error fetching review items:', err);
        setError('Failed to load review items. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchItems();
  }, [selectedClient]);

  // Auto-select first item on load
  useEffect(() => {
    if (items.length > 0 && !selectedItem) {
      setSelectedItem(items[0]);
    }
  }, [items, selectedItem]);

  // Filter items
  const filteredItems = items.filter(item => {
    if (selectedStatus && item.status !== selectedStatus) return false;
    if (selectedPriority && item.priority !== selectedPriority) return false;
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        item.supplier.toLowerCase().includes(query) ||
        item.description.toLowerCase().includes(query) ||
        item.invoiceNumber?.toLowerCase().includes(query)
      );
    }
    return true;
  });

  // Sort by priority and date
  const sortedItems = [...filteredItems].sort((a, b) => {
    const priorityOrder = { high: 0, medium: 1, low: 2 };
    if (priorityOrder[a.priority] !== priorityOrder[b.priority]) {
      return priorityOrder[a.priority] - priorityOrder[b.priority];
    }
    return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
  });

  // Polling for real-time updates
  useEffect(() => {
    if (!selectedClient?.id) return;

    const interval = setInterval(async () => {
      try {
        const data = await reviewQueueApi.getReviewItems({ client_id: selectedClient.id });
        const itemsArray = Array.isArray(data) ? data : ((data as any).items || []);
        setItems(itemsArray);
      } catch (err) {
        console.error('Error polling review items:', err);
      }
    }, 30000); // Poll every 30 seconds

    return () => clearInterval(interval);
  }, [selectedClient]);

  const handleApprove = async (id: string) => {
    try {
      await reviewQueueApi.approveItem(id);
      
      // Update local state
      setItems(items.map(item => 
        item.id === id 
          ? { ...item, status: 'approved' as ReviewStatus, reviewedAt: new Date().toISOString(), reviewedBy: 'current.user' }
          : item
      ));

      if (selectedItem?.id === id) {
        const updated = items.find(i => i.id === id);
        if (updated) {
          setSelectedItem({ ...updated, status: 'approved' as ReviewStatus, reviewedAt: new Date().toISOString() });
        }
      }
    } catch (err) {
      console.error('Error approving item:', err);
      toast.error('Failed to approve item. Please try again.');
    }
  };

  const handleCorrect = async (id: string, corrections: any) => {
    try {
      await reviewQueueApi.correctItem(id, corrections);
      
      // Update local state
      setItems(items.map(item => 
        item.id === id 
          ? { ...item, ...corrections, status: 'corrected' as ReviewStatus, reviewedAt: new Date().toISOString(), reviewedBy: 'current.user' }
          : item
      ));

      if (selectedItem?.id === id) {
        const updated = items.find(i => i.id === id);
        if (updated) {
          setSelectedItem({ ...updated, ...corrections, status: 'corrected' as ReviewStatus });
        }
      }
    } catch (err) {
      console.error('Error correcting item:', err);
      toast.error('Failed to correct item. Please try again.');
    }
  };

  const handleSendMessage = async (message: string) => {
    const userMessage: ChatMessage = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    };

    setChatMessages([...chatMessages, userMessage]);

    // Simulate AI response
    await new Promise(resolve => setTimeout(resolve, 1000));

    const aiMessage: ChatMessage = {
      role: 'assistant',
      content: 'Dette er en simulert AI-respons. I produksjon ville dette vært en ekte analyse av fakturaen.',
      timestamp: new Date().toISOString(),
    };

    setChatMessages(prev => [...prev, aiMessage]);
  };

  // Show loading when client is loading
  if (clientLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <p className="mt-2 text-muted-foreground">Laster klient...</p>
        </div>
      </div>
    );
  }

  // Show message when no client is selected
  if (!selectedClient) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-lg text-muted-foreground">
            Velg en klient fra menyen øverst for å se behandlingskø
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Left Column - List */}
      <div className="lg:col-span-1 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-100">
            Review Queue ({sortedItems.length})
          </h2>
          <button className="px-4 py-2 bg-accent-blue hover:bg-blue-600 text-white rounded-lg text-sm font-medium transition-colors">
            + Ny faktura
          </button>
        </div>

        <FilterBar
          selectedStatus={selectedStatus}
          selectedPriority={selectedPriority}
          onStatusChange={setSelectedStatus}
          onPriorityChange={setSelectedPriority}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
        />

        <div className="space-y-3 max-h-[calc(100vh-400px)] overflow-y-auto scrollbar-thin">
          {sortedItems.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              Ingen fakturaer funnet
            </div>
          ) : (
            sortedItems.map(item => (
              <ReviewQueueItem
                key={item.id}
                item={item}
                onClick={() => setSelectedItem(item)}
                isSelected={selectedItem?.id === item.id}
              />
            ))
          )}
        </div>
      </div>

      {/* Right Column - Details */}
      <div className="lg:col-span-2 space-y-4">
        {selectedItem ? (
          <>
            <InvoiceDetails item={selectedItem} />

            {/* Tabs */}
            <div className="flex gap-2 border-b border-dark-border">
              {(['details', 'chat', 'patterns'] as const).map(tab => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-4 py-2 font-medium transition-colors ${
                    activeTab === tab
                      ? 'text-accent-blue border-b-2 border-accent-blue'
                      : 'text-gray-400 hover:text-gray-300'
                  }`}
                >
                  {tab === 'details' && 'Posteringer'}
                  {tab === 'chat' && 'AI Chat'}
                  {tab === 'patterns' && 'Mønstre'}
                </button>
              ))}
            </div>

            {/* Tab Content */}
            <div>
              {activeTab === 'details' && (
                <BookingDetails bookings={selectedItem.bookingEntries} />
              )}
              {activeTab === 'chat' && (
                <ChatInterface
                  itemId={selectedItem.id}
                  messages={chatMessages}
                  onSendMessage={handleSendMessage}
                />
              )}
              {activeTab === 'patterns' && (
                <div className="bg-dark-card border border-dark-border rounded-lg p-6">
                  <h3 className="font-semibold text-gray-100 mb-4">Foreslåtte mønstre</h3>
                  <PatternList patterns={selectedItem.suggestedPatterns} />
                </div>
              )}
            </div>

            {/* Actions */}
            {selectedItem.status === 'pending' && (
              <div className="flex gap-3 justify-end">
                <ApproveButton
                  itemId={selectedItem.id}
                  onApprove={handleApprove}
                />
                <CorrectButton
                  itemId={selectedItem.id}
                  currentBookings={selectedItem.bookingEntries}
                  onCorrect={handleCorrect}
                />
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-24 text-gray-500">
            Velg en faktura for å se detaljer
          </div>
        )}
      </div>
    </div>
  );
};
