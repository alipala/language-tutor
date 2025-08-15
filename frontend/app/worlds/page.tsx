'use client';

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/lib/auth';
import { worldBuildingAPI, type StoryWorld, type WorldFilters } from '@/lib/world-building-api';
import WorldCard from '@/components/world-building/WorldCard';
import WorldFiltersComponent from '@/components/world-building/WorldFilters';
import WorldDetailsModal from '@/components/world-building/WorldDetailsModal';
import StoryCreationModal from '@/components/world-building/StoryCreationModal';
import { Search, Filter, Globe, Sparkles, TrendingUp } from 'lucide-react';
import { useSearchParams, useRouter } from 'next/navigation';

export default function WorldsDiscoveryPage() {
  const { user } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // State management
  const [worlds, setWorlds] = useState<StoryWorld[]>([]);
  const [featuredWorlds, setFeaturedWorlds] = useState<StoryWorld[]>([]);
  const [trendingWorlds, setTrendingWorlds] = useState<StoryWorld[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchLoading, setSearchLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [featureEnabled, setFeatureEnabled] = useState(false);
  
  // Pagination and filtering
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalWorlds, setTotalWorlds] = useState(0);
  const [hasNext, setHasNext] = useState(false);
  const [hasPrev, setHasPrev] = useState(false);
  
  // UI state
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearchQuery, setDebouncedSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [selectedWorld, setSelectedWorld] = useState<StoryWorld | null>(null);
  const [activeTab, setActiveTab] = useState<'discover' | 'featured' | 'trending'>('discover');
  const [showCreateModal, setShowCreateModal] = useState(false);
  
  // Filters state
  const [filters, setFilters] = useState<WorldFilters>({
    language: [],
    target_level: [],
    genre: [],
    status: ['active'],
    sort_by: 'created_at',
    sort_order: 'desc'
  });

  // Initialize from URL parameters
  useEffect(() => {
    const urlSearch = searchParams.get('search');
    const urlLanguage = searchParams.getAll('language');
    const urlLevel = searchParams.getAll('level');
    const urlGenre = searchParams.getAll('genre');
    const urlTab = searchParams.get('tab') as 'discover' | 'featured' | 'trending' | null;
    
    if (urlSearch) {
      setSearchQuery(urlSearch);
      setDebouncedSearchQuery(urlSearch);
    }
    
    if (urlTab && ['discover', 'featured', 'trending'].includes(urlTab)) {
      setActiveTab(urlTab);
    }
    
    setFilters(prev => ({
      ...prev,
      ...(urlLanguage.length && { language: urlLanguage }),
      ...(urlLevel.length && { target_level: urlLevel }),
      ...(urlGenre.length && { genre: urlGenre }),
      ...(urlSearch && { search: urlSearch })
    }));
  }, [searchParams]);

  // Debounce search query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchQuery(searchQuery);
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Update URL when filters change
  const updateURL = useCallback((newFilters: WorldFilters, newSearch: string, newTab: string) => {
    const params = new URLSearchParams();
    
    if (newSearch) params.set('search', newSearch);
    if (newTab !== 'discover') params.set('tab', newTab);
    
    newFilters.language?.forEach(lang => params.append('language', lang));
    newFilters.target_level?.forEach(level => params.append('level', level));
    newFilters.genre?.forEach(genre => params.append('genre', genre));
    
    const newURL = params.toString() ? `?${params.toString()}` : '';
    router.replace(`/worlds${newURL}`, { scroll: false });
  }, [router]);

  // Check if feature is enabled
  useEffect(() => {
    const checkFeature = async () => {
      try {
        const enabled = await worldBuildingAPI.checkFeatureEnabled();
        setFeatureEnabled(enabled);
        
        if (!enabled) {
          setError('World Building feature is not currently available.');
          setLoading(false);
        }
      } catch (err) {
        console.error('Error checking feature status:', err);
        setError('Unable to check feature availability.');
        setLoading(false);
      }
    };
    
    checkFeature();
  }, []);

  // Load initial data
  useEffect(() => {
    if (!featureEnabled) return;
    
    const loadInitialData = async () => {
      try {
        setLoading(true);
        
        // Load featured and trending worlds in parallel
        const [featuredResponse, trendingResponse] = await Promise.all([
          worldBuildingAPI.getFeaturedWorlds(6),
          worldBuildingAPI.getTrendingWorlds(6)
        ]);
        
        setFeaturedWorlds(featuredResponse);
        setTrendingWorlds(trendingResponse);
        
        // Load main discovery data
        await loadWorlds();
        
      } catch (err) {
        console.error('Error loading initial data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load worlds');
      } finally {
        setLoading(false);
      }
    };
    
    loadInitialData();
  }, [featureEnabled]);

  // Load worlds based on current filters and search
  const loadWorlds = useCallback(async (page: number = 1) => {
    if (!featureEnabled) return;
    
    try {
      setSearchLoading(true);
      setError(null);
      
      const searchFilters = {
        ...filters,
        search: debouncedSearchQuery || undefined
      };
      
      const response = await worldBuildingAPI.discoverWorlds(searchFilters, page, 12);
      
      setWorlds(response.worlds);
      setCurrentPage(response.page);
      setTotalPages(Math.ceil(response.total / 12));
      setTotalWorlds(response.total);
      setHasNext(response.has_next);
      setHasPrev(response.has_prev);
      
    } catch (err) {
      console.error('Error loading worlds:', err);
      setError(err instanceof Error ? err.message : 'Failed to load worlds');
    } finally {
      setSearchLoading(false);
    }
  }, [featureEnabled, filters, debouncedSearchQuery]);

  // Reload worlds when filters or search change
  useEffect(() => {
    if (featureEnabled && activeTab === 'discover') {
      loadWorlds(1);
      setCurrentPage(1);
    }
  }, [featureEnabled, filters, debouncedSearchQuery, activeTab, loadWorlds]);

  // Update URL when filters or search change
  useEffect(() => {
    updateURL(filters, debouncedSearchQuery, activeTab);
  }, [filters, debouncedSearchQuery, activeTab, updateURL]);

  // Handle filter changes
  const handleFiltersChange = (newFilters: WorldFilters) => {
    setFilters(newFilters);
  };

  // Handle search
  const handleSearch = (query: string) => {
    setSearchQuery(query);
    setActiveTab('discover'); // Switch to discover tab when searching
  };

  // Handle pagination
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    loadWorlds(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Handle world card click
  const handleWorldClick = (world: StoryWorld) => {
    setSelectedWorld(world);
  };

  // Handle story creation
  const handleCreateStory = () => {
    setShowCreateModal(true);
  };

  // Handle story creation success
  const handleStoryCreated = (worldId: string) => {
    setShowCreateModal(false);
    // Refresh the worlds list to show the new story
    loadWorlds(1);
    setCurrentPage(1);
    // Stay on the main worlds page - don't navigate to individual world
    // The newly created story will appear in the list after refresh
  };

  // Get current worlds to display based on active tab
  const getCurrentWorlds = () => {
    switch (activeTab) {
      case 'featured':
        return featuredWorlds;
      case 'trending':
        return trendingWorlds;
      default:
        return worlds;
    }
  };

  // Show loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#4ECFBF]/10 to-[#FFD63A]/10">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#4ECFBF] mx-auto mb-4"></div>
            <p className="text-gray-600">Loading story worlds...</p>
          </div>
        </div>
      </div>
    );
  }

  // Show error state
  if (error && !featureEnabled) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#4ECFBF]/10 to-[#FFD63A]/10">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center py-20">
            <Globe className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-800 mb-2">World Building Coming Soon</h2>
            <p className="text-gray-600 mb-4">This feature is currently being developed.</p>
            <button
              onClick={() => router.push('/profile')}
              className="bg-[#4ECFBF] text-white px-6 py-2 rounded-lg hover:bg-[#3a9e92] transition-colors"
            >
              Return to Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-br from-[#4ECFBF]/10 to-[#FFD63A]/10 navbar-compensated">
      <div className="flex min-h-screen">
        {/* Fixed Left Sidebar - Filters - Positioned lower to align with content */}
        <div className="w-80 flex-shrink-0 bg-white border-r border-gray-200">
          <div className="pt-8">
            <div className="sticky top-28">
              <WorldFiltersComponent
                filters={filters}
                onFiltersChange={handleFiltersChange}
                onClose={() => {}} // No close needed since it's always visible
                isAuthenticated={!!user}
                onCreateStory={handleCreateStory}
                currentUserId={user?._id}
              />
            </div>
          </div>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 min-h-screen">
          <div className="container mx-auto px-6 py-8">
            {/* Header */}
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold text-gray-800 mb-2 flex items-center justify-center gap-3">
                <Globe className="h-10 w-10 text-[#4ECFBF]" />
                Discover Story Worlds
              </h1>
              <p className="text-gray-600 text-lg max-w-2xl mx-auto">
                Explore collaborative storytelling worlds where you can practice languages through immersive narratives
              </p>
            </div>

            {/* Search Bar - Fixed placeholder text color */}
            <div className="max-w-2xl mx-auto mb-8">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
                <input
                  type="text"
                  placeholder="Search story worlds..."
                  value={searchQuery}
                  onChange={(e) => handleSearch(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent placeholder:text-gray-500"
                />
              </div>
            </div>

            {/* Tabs */}
            <div className="flex justify-center mb-6">
              <div className="flex bg-white rounded-lg p-1 shadow-sm">
                <button
                  onClick={() => setActiveTab('discover')}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === 'discover'
                      ? 'bg-[#4ECFBF] text-white'
                      : 'text-gray-600 hover:text-gray-800'
                  }`}
                >
                  <Globe className="h-4 w-4 inline mr-2" />
                  Discover
                </button>
                <button
                  onClick={() => setActiveTab('featured')}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === 'featured'
                      ? 'bg-[#FFD63A] text-white'
                      : 'text-gray-600 hover:text-gray-800'
                  }`}
                >
                  <Sparkles className="h-4 w-4 inline mr-2" />
                  Featured
                </button>
                <button
                  onClick={() => setActiveTab('trending')}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === 'trending'
                      ? 'bg-[#F75A5A] text-white'
                      : 'text-gray-600 hover:text-gray-800'
                  }`}
                >
                  <TrendingUp className="h-4 w-4 inline mr-2" />
                  Trending
                </button>
              </div>
            </div>

            {/* Results Info */}
            {activeTab === 'discover' && (
              <div className="flex justify-between items-center mb-6">
                <p className="text-gray-800">
                  {searchLoading ? 'Searching...' : `${totalWorlds} worlds found`}
                </p>
                {totalPages > 1 && (
                  <p className="text-gray-800">
                    Page {currentPage} of {totalPages}
                  </p>
                )}
              </div>
            )}

            {/* Loading State */}
            {searchLoading && (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#4ECFBF] mx-auto mb-2"></div>
                <p className="text-gray-600">Loading worlds...</p>
              </div>
            )}

            {/* Error State */}
            {error && featureEnabled && (
              <div className="text-center py-8">
                <p className="text-red-600 mb-4">{error}</p>
                <button
                  onClick={() => loadWorlds(currentPage)}
                  className="bg-[#4ECFBF] text-white px-4 py-2 rounded-lg hover:bg-[#3a9e92] transition-colors"
                >
                  Try Again
                </button>
              </div>
            )}

            {/* Worlds Grid */}
            {!searchLoading && !error && (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                  {getCurrentWorlds().map((world) => (
                    <WorldCard
                      key={world.id}
                      world={world}
                      onClick={() => handleWorldClick(world)}
                    />
                  ))}
                </div>

                {/* Empty State */}
                {getCurrentWorlds().length === 0 && (
                  <div className="text-center py-12">
                    <Globe className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-gray-800 mb-2">No worlds found</h3>
                    <p className="text-gray-600 mb-4">
                      {activeTab === 'discover' && (debouncedSearchQuery || filters.language?.length || filters.target_level?.length || filters.genre?.length)
                        ? 'Try adjusting your search or filters'
                        : activeTab === 'featured'
                        ? 'No featured worlds available at the moment'
                        : activeTab === 'trending'
                        ? 'No trending worlds available at the moment'
                        : 'No worlds available at the moment'
                      }
                    </p>
                    {(debouncedSearchQuery || filters.language?.length || filters.target_level?.length || filters.genre?.length) && (
                      <button
                        onClick={() => {
                          setSearchQuery('');
                          setFilters({
                            language: [],
                            target_level: [],
                            genre: [],
                            status: ['active'],
                            sort_by: 'created_at',
                            sort_order: 'desc'
                          });
                        }}
                        className="bg-[#4ECFBF] text-white px-4 py-2 rounded-lg hover:bg-[#3a9e92] transition-colors"
                      >
                        Clear Filters
                      </button>
                    )}
                  </div>
                )}
              </>
            )}

            {/* Enhanced Pagination */}
            {activeTab === 'discover' && totalPages > 1 && !searchLoading && (
              <div className="bg-white rounded-lg border border-gray-200 p-4 mt-8">
                <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
                  {/* Results Summary */}
                  <div className="text-sm text-gray-600">
                    Showing {((currentPage - 1) * 12) + 1} to {Math.min(currentPage * 12, totalWorlds)} of {totalWorlds} worlds
                  </div>
                  
                  {/* Pagination Controls */}
                  <div className="flex items-center gap-2">
                    {/* First Page */}
                    {currentPage > 3 && (
                      <>
                        <button
                          onClick={() => handlePageChange(1)}
                          className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-sm text-gray-700 hover:text-gray-900"
                        >
                          1
                        </button>
                        {currentPage > 4 && (
                          <span className="px-2 text-gray-400">...</span>
                        )}
                      </>
                    )}
                    
                    {/* Previous Button */}
                    <button
                      onClick={() => handlePageChange(currentPage - 1)}
                      disabled={!hasPrev}
                      className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors text-sm font-medium text-gray-700 hover:text-gray-900"
                    >
                      Previous
                    </button>
                    
                    {/* Page Numbers */}
                    <div className="flex gap-1">
                      {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                        const pageNum = Math.max(1, Math.min(totalPages - 4, currentPage - 2)) + i;
                        return (
                          <button
                            key={pageNum}
                            onClick={() => handlePageChange(pageNum)}
                            className={`px-3 py-2 rounded-lg transition-colors text-sm font-medium ${
                              pageNum === currentPage
                                ? 'bg-[#4ECFBF] text-white shadow-md'
                                : 'border border-gray-300 hover:bg-gray-50 text-gray-700 hover:text-gray-900'
                            }`}
                          >
                            {pageNum}
                          </button>
                        );
                      })}
                    </div>
                    
                    {/* Next Button */}
                    <button
                      onClick={() => handlePageChange(currentPage + 1)}
                      disabled={!hasNext}
                      className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors text-sm font-medium text-gray-700 hover:text-gray-900"
                    >
                      Next
                    </button>
                    
                    {/* Last Page */}
                    {currentPage < totalPages - 2 && (
                      <>
                        {currentPage < totalPages - 3 && (
                          <span className="px-2 text-gray-400">...</span>
                        )}
                        <button
                          onClick={() => handlePageChange(totalPages)}
                          className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-sm text-gray-700 hover:text-gray-900"
                        >
                          {totalPages}
                        </button>
                      </>
                    )}
                  </div>
                  
                  {/* Quick Jump */}
                  {totalPages > 10 && (
                    <div className="flex items-center gap-2 text-sm">
                      <span className="text-gray-600">Go to:</span>
                      <input
                        type="number"
                        min="1"
                        max={totalPages}
                        value={currentPage}
                        onChange={(e) => {
                          const page = parseInt(e.target.value);
                          if (page >= 1 && page <= totalPages) {
                            handlePageChange(page);
                          }
                        }}
                        className="w-16 px-2 py-1 border border-gray-300 rounded text-center focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent"
                      />
                      <span className="text-gray-600">of {totalPages}</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* World Details Modal */}
      {selectedWorld && (
        <WorldDetailsModal
          world={selectedWorld}
          isOpen={!!selectedWorld}
          onClose={() => setSelectedWorld(null)}
        />
      )}

      {/* Story Creation Modal */}
      <StoryCreationModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={handleStoryCreated}
      />
    </div>
  );
}
