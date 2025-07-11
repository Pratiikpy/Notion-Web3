import React, { useState, useEffect } from 'react';
import { ethers } from 'ethers';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Glass Card Component
const GlassCard = ({ children, className = "", ...props }) => (
  <div className={`glass-card ${className}`} {...props}>
    {children}
  </div>
);

// Neon Button Component
const NeonButton = ({ children, onClick, disabled = false, variant = "primary", className = "", ...props }) => (
  <button
    onClick={onClick}
    disabled={disabled}
    className={`neon-button ${variant} ${className} ${disabled ? 'disabled' : ''}`}
    {...props}
  >
    {children}
  </button>
);

// Loading Spinner Component
const LoadingSpinner = ({ size = "md" }) => (
  <div className={`loading-spinner ${size}`}>
    <div className="spinner"></div>
  </div>
);

// Comment System Component
const CommentSystem = ({ snippetId, userAddress, isOpen, onClose }) => {
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isOpen && snippetId) {
      fetchComments();
    }
  }, [isOpen, snippetId]);

  const fetchComments = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`${API}/social/comments/${snippetId}`);
      if (!response.ok) throw new Error('Failed to fetch comments');
      const data = await response.json();
      setComments(data.comments || []);
    } catch (error) {
      console.error('Error fetching comments:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmitComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim() || !userAddress) return;

    try {
      setIsSubmitting(true);
      const response = await fetch(`${API}/social/comment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_address: userAddress,
          snippet_id: snippetId,
          content: newComment.trim()
        })
      });

      if (response.ok) {
        setNewComment('');
        fetchComments(); // Refresh comments
      }
    } catch (error) {
      console.error('Error submitting comment:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="comment-modal-overlay" onClick={onClose}>
      <div className="comment-modal" onClick={(e) => e.stopPropagation()}>
        <div className="comment-header">
          <h3>💬 Comments</h3>
          <button onClick={onClose} className="close-button">×</button>
        </div>

        <div className="comment-content">
          {isLoading ? (
            <div className="comment-loading">
              <LoadingSpinner size="md" />
              <p>Loading comments...</p>
            </div>
          ) : (
            <div className="comments-list">
              {comments.length === 0 ? (
                <p className="no-comments">No comments yet. Be the first to comment!</p>
              ) : (
                comments.map((comment) => (
                  <div key={comment.id} className="comment-item">
                    <div className="comment-author">
                      <span className="comment-username">
                        {comment.username || `${comment.user_address.slice(0, 6)}...${comment.user_address.slice(-4)}`}
                      </span>
                      <span className="comment-date">
                        {new Date(comment.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <p className="comment-text">{comment.content}</p>
                  </div>
                ))
              )}
            </div>
          )}

          {userAddress && (
            <form onSubmit={handleSubmitComment} className="comment-form">
              <textarea
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="Write a comment..."
                className="comment-input"
                rows="3"
                disabled={isSubmitting}
              />
              <NeonButton
                type="submit"
                disabled={!newComment.trim() || isSubmitting}
                className="comment-submit"
              >
                {isSubmitting ? <LoadingSpinner size="sm" /> : 'Post Comment'}
              </NeonButton>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

// Navigation Component
const Navigation = ({ currentTab, onTabChange, userAddress }) => {
  const tabs = [
    { id: 'home', label: 'Home', icon: '🏠' },
    { id: 'feed', label: 'Feed', icon: '📰' },
    { id: 'profile', label: 'Profile', icon: '👤' },
    { id: 'discover', label: 'Discover', icon: '🔍' }
  ];

  return (
    <div className="navigation">
      <div className="nav-tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`nav-tab ${currentTab === tab.id ? 'active' : ''}`}
          >
            <span className="tab-icon">{tab.icon}</span>
            <span className="tab-label">{tab.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

// Public Feed Component
const PublicFeed = ({ userAddress }) => {
  const [feed, setFeed] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [commentModalOpen, setCommentModalOpen] = useState(false);
  const [selectedSnippetId, setSelectedSnippetId] = useState(null);

  useEffect(() => {
    fetchPublicFeed();
  }, []);

  const fetchPublicFeed = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await fetch(`${API}/feed/public`);
      if (!response.ok) throw new Error('Failed to fetch feed');
      const data = await response.json();
      setFeed(data.feed || []);
    } catch (error) {
      console.error('Error fetching public feed:', error);
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLike = async (snippetId) => {
    if (!userAddress) return;
    
    try {
      const response = await fetch(`${API}/social/like`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_address: userAddress,
          snippet_id: snippetId
        })
      });
      
      if (response.ok) {
        // Refresh feed to update like status
        fetchPublicFeed();
      }
    } catch (error) {
      console.error('Error liking snippet:', error);
    }
  };

  const handleOpenComments = (snippetId) => {
    setSelectedSnippetId(snippetId);
    setCommentModalOpen(true);
  };

  const handleCloseComments = () => {
    setCommentModalOpen(false);
    setSelectedSnippetId(null);
    // Refresh feed to update comment count
    fetchPublicFeed();
  };

  if (isLoading) {
    return (
      <div className="feed-container">
        <div className="loading-container">
          <LoadingSpinner size="lg" />
          <p>Loading public feed...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="feed-container">
        <div className="error-container">
          <p>Error loading feed: {error}</p>
          <NeonButton onClick={fetchPublicFeed}>Try Again</NeonButton>
        </div>
      </div>
    );
  }

  return (
    <div className="feed-container">
      <div className="feed-header">
        <h2>🌐 Public Feed</h2>
        <p>Discover snippets from the community</p>
      </div>
      
      {feed.length === 0 ? (
        <div className="empty-feed">
          <p>No snippets in the feed yet. Be the first to share!</p>
        </div>
      ) : (
        <div className="feed-grid">
          {feed.map((snippet) => (
            <GlassCard key={snippet.id} className="feed-item">
              <div className="snippet-header">
                <div className="user-info">
                  <span className="username">
                    {snippet.username || `${snippet.wallet_address.slice(0, 6)}...${snippet.wallet_address.slice(-4)}`}
                  </span>
                  <span className="timestamp">
                    {new Date(snippet.created_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="content-type-indicator">
                  <span className="content-type-badge">
                    {snippet.content_type === 'web_snippet' && '🔗'} 
                    {snippet.content_type === 'text' && '📝'}
                    {snippet.content_type === 'poetry' && '🎭'}
                    {snippet.content_type === 'image' && '🖼️'}
                    {snippet.content_type === 'quote' && '💬'}
                    {snippet.content_type || 'web_snippet'}
                  </span>
                  <span className="network-badge">{snippet.network}</span>
                </div>
              </div>
              
              <h3 className="snippet-title">{snippet.title}</h3>
              <p className="snippet-summary">{snippet.summary}</p>
              
              {snippet.mood && (
                <div className="content-metadata">
                  <span className="mood-indicator">😊 {snippet.mood}</span>
                  {snippet.theme && <span className="theme-indicator">🎯 {snippet.theme}</span>}
                </div>
              )}
              
              <div className="snippet-tags">
                {snippet.tags && snippet.tags.map((tag, index) => (
                  <span key={index} className="tag">{tag}</span>
                ))}
              </div>
              
              <div className="snippet-actions">
                {snippet.url && (
                  <button 
                    onClick={() => window.open(snippet.url, '_blank')}
                    className="action-button"
                  >
                    🔗 View
                  </button>
                )}
                <button 
                  onClick={() => handleLike(snippet.irys_id)}
                  className={`action-button like-button ${snippet.is_liked ? 'liked' : ''}`}
                >
                  ❤️ {snippet.likes_count || 0}
                </button>
                <button 
                  onClick={() => handleOpenComments(snippet.irys_id)}
                  className="action-button"
                >
                  💬 {snippet.comments_count || 0}
                </button>
                <button 
                  onClick={() => window.open(snippet.network === 'devnet' ? `https://devnet.irys.xyz/${snippet.irys_id}` : `https://gateway.irys.xyz/${snippet.irys_id}`, '_blank')}
                  className="action-button blockchain-button"
                >
                  ⛓️ Blockchain
                </button>
              </div>
            </GlassCard>
          ))}
        </div>
      )}

      <CommentSystem
        snippetId={selectedSnippetId}
        userAddress={userAddress}
        isOpen={commentModalOpen}
        onClose={handleCloseComments}
      />
    </div>
  );
};

// User Profile Component
const UserProfile = ({ userAddress, signer }) => {
  const [profile, setProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({ username: '', bio: '' });

  useEffect(() => {
    if (userAddress) {
      fetchProfile();
    }
  }, [userAddress]);

  const fetchProfile = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`${API}/users/${userAddress}`);
      if (!response.ok) throw new Error('Failed to fetch profile');
      const data = await response.json();
      setProfile(data);
      setEditForm({ username: data.username || '', bio: data.bio || '' });
    } catch (error) {
      console.error('Error fetching profile:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveProfile = async () => {
    try {
      const response = await fetch(`${API}/users/profile`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          wallet_address: userAddress,
          username: editForm.username,
          bio: editForm.bio
        })
      });
      
      if (response.ok) {
        setIsEditing(false);
        fetchProfile();
      }
    } catch (error) {
      console.error('Error saving profile:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="profile-container">
        <div className="loading-container">
          <LoadingSpinner size="lg" />
          <p>Loading profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="profile-container">
      <GlassCard className="profile-card">
        <div className="profile-header">
          <div className="profile-avatar">
            {profile.username ? profile.username.charAt(0).toUpperCase() : '👤'}
          </div>
          <div className="profile-info">
            {isEditing ? (
              <div className="edit-form">
                <input
                  type="text"
                  value={editForm.username}
                  onChange={(e) => setEditForm({...editForm, username: e.target.value})}
                  placeholder="Username"
                  className="edit-input"
                />
                <textarea
                  value={editForm.bio}
                  onChange={(e) => setEditForm({...editForm, bio: e.target.value})}
                  placeholder="Bio"
                  className="edit-textarea"
                />
                <div className="edit-actions">
                  <NeonButton onClick={handleSaveProfile}>Save</NeonButton>
                  <NeonButton variant="secondary" onClick={() => setIsEditing(false)}>Cancel</NeonButton>
                </div>
              </div>
            ) : (
              <div className="profile-display">
                <h2>{profile.username || 'Anonymous User'}</h2>
                <p className="wallet-address">{userAddress}</p>
                <p className="bio">{profile.bio || 'No bio set'}</p>
                <NeonButton onClick={() => setIsEditing(true)}>Edit Profile</NeonButton>
              </div>
            )}
          </div>
        </div>
        
        <div className="profile-stats">
          <div className="stat">
            <span className="stat-number">{profile.snippets_count || 0}</span>
            <span className="stat-label">Snippets</span>
          </div>
          <div className="stat">
            <span className="stat-number">{profile.followers_count || 0}</span>
            <span className="stat-label">Followers</span>
          </div>
          <div className="stat">
            <span className="stat-number">{profile.following_count || 0}</span>
            <span className="stat-label">Following</span>
          </div>
        </div>
      </GlassCard>
    </div>
  );
};

// User Discovery Component
const UserDiscovery = ({ userAddress }) => {
  const [users, setUsers] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`${API}/users/discover`);
      if (!response.ok) throw new Error('Failed to fetch users');
      const data = await response.json();
      setUsers(data.users || []);
    } catch (error) {
      console.error('Error fetching users:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFollow = async (targetAddress) => {
    if (!userAddress) return;
    
    try {
      const response = await fetch(`${API}/social/follow`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          follower_address: userAddress,
          following_address: targetAddress
        })
      });
      
      if (response.ok) {
        // Refresh users list
        fetchUsers();
      }
    } catch (error) {
      console.error('Error following user:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="discovery-container">
        <div className="loading-container">
          <LoadingSpinner size="lg" />
          <p>Discovering users...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="discovery-container">
      <div className="discovery-header">
        <h2>🔍 Discover Users</h2>
        <p>Find and follow other snippet creators</p>
      </div>
      
      {users.length === 0 ? (
        <div className="empty-discovery">
          <p>No users to discover yet.</p>
        </div>
      ) : (
        <div className="users-grid">
          {users.map((user) => (
            <GlassCard key={user.wallet_address} className="user-card">
              <div className="user-avatar">
                {user.username ? user.username.charAt(0).toUpperCase() : '👤'}
              </div>
              <h3>{user.username || 'Anonymous User'}</h3>
              <p className="user-wallet">
                {user.wallet_address.slice(0, 6)}...{user.wallet_address.slice(-4)}
              </p>
              <p className="user-bio">{user.bio || 'No bio'}</p>
              
              <div className="user-stats">
                <span>{user.snippets_count || 0} snippets</span>
                <span>{user.followers_count || 0} followers</span>
              </div>
              
              {user.wallet_address !== userAddress && (
                <NeonButton 
                  onClick={() => handleFollow(user.wallet_address)}
                  className="follow-button"
                >
                  Follow
                </NeonButton>
              )}
            </GlassCard>
          ))}
        </div>
      )}
    </div>
  );
};

// Real Irys Integration Helper
const createIrysUploader = async (signer) => {
  try {
    // For simplicity, we'll use the backend to handle Irys uploads
    // since browser Irys SDK has complex polyfill requirements
    const address = await signer.getAddress();
    return {
      address,
      signer,
      upload: async (data, options = {}) => {
        // Create a message for the user to sign
        const message = `Upload to Irys blockchain:\nData: ${data.substring(0, 100)}${data.length > 100 ? '...' : ''}\nTimestamp: ${Date.now()}`;
        const signature = await signer.signMessage(message);
        
        // Send to backend for real Irys upload
        const response = await fetch(`${API}/irys-upload`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            data,
            signature,
            address,
            tags: options.tags || []
          })
        });
        
        if (!response.ok) {
          throw new Error('Failed to upload to Irys');
        }
        
        return await response.json();
      }
    };
  } catch (error) {
    console.error('Error creating Irys uploader:', error);
    throw error;
  }
};

// Wallet Connection Component
const WalletConnection = ({ onWalletConnected, connectedWallet, balance }) => {
  const [isConnecting, setIsConnecting] = useState(false);

  const connectWallet = async () => {
    if (!window.ethereum) {
      alert("Please install MetaMask to use this application!");
      return;
    }

    try {
      setIsConnecting(true);
      const provider = new ethers.BrowserProvider(window.ethereum);
      await provider.send("eth_requestAccounts", []);
      const signer = await provider.getSigner();
      const walletAddress = await signer.getAddress();
      
      onWalletConnected(signer, walletAddress);
    } catch (error) {
      console.error("Wallet connection failed:", error);
      alert("Failed to connect wallet. Please try again.");
    } finally {
      setIsConnecting(false);
    }
  };

  return (
    <div className="wallet-connection">
      {connectedWallet ? (
        <div className="connected-wallet">
          <div className="wallet-indicator"></div>
          <div className="wallet-info">
            <span className="wallet-address">
              {connectedWallet.slice(0, 6)}...{connectedWallet.slice(-4)}
            </span>
            {balance && (
              <span className="wallet-balance">
                Balance: {balance} ETH
              </span>
            )}
          </div>
        </div>
      ) : (
        <NeonButton onClick={connectWallet} disabled={isConnecting}>
          {isConnecting ? <LoadingSpinner size="sm" /> : "Connect Wallet"}
        </NeonButton>
      )}
    </div>
  );
};

// Enhanced Snippet Form Component with Content Types
const SnippetForm = ({ signer, userAddress, onSnippetSaved }) => {
  const [contentType, setContentType] = useState('web_snippet');
  const [url, setUrl] = useState('');
  const [textContent, setTextContent] = useState('');
  const [textTitle, setTextTitle] = useState('');
  const [imageFile, setImageFile] = useState(null);
  const [imageTitle, setImageTitle] = useState('');
  const [imageDescription, setImageDescription] = useState('');
  const [extractedData, setExtractedData] = useState(null);
  const [summarizedData, setSummarizedData] = useState(null);
  const [network, setNetwork] = useState('devnet');
  const [isExtracting, setIsExtracting] = useState(false);
  const [isSummarizing, setIsSummarizing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [irysUploader, setIrysUploader] = useState(null);

  useEffect(() => {
    if (signer) {
      createIrysUploader(signer).then(setIrysUploader).catch(console.error);
    }
  }, [signer]);

  const contentTypes = [
    { id: 'web_snippet', label: 'Web Snippet', icon: '🔗', description: 'Extract content from any webpage' },
    { id: 'text', label: 'Text/Poetry', icon: '📝', description: 'Write poems, thoughts, or stories' },
    { id: 'image', label: 'Image', icon: '🖼️', description: 'Upload and describe images' }
  ];

  const resetForm = () => {
    setUrl('');
    setTextContent('');
    setTextTitle('');
    setImageFile(null);
    setImageTitle('');
    setImageDescription('');
    setExtractedData(null);
    setSummarizedData(null);
  };

  const handleContentTypeChange = (type) => {
    setContentType(type);
    resetForm();
  };

  const extractSnippet = async () => {
    if (!url.trim()) return;
    
    try {
      setIsExtracting(true);
      const response = await fetch(`${API}/extract-snippet`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url.trim() })
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to extract snippet');
      }
      
      const data = await response.json();
      setExtractedData(data);
      
      // Auto-summarize after extraction
      summarizeContent(data);
    } catch (error) {
      console.error('Error extracting snippet:', error);
      alert(`Error extracting snippet: ${error.message}`);
    } finally {
      setIsExtracting(false);
    }
  };

  const processTextContent = async () => {
    if (!textContent.trim() || !textTitle.trim()) {
      alert('Please enter both title and content');
      return;
    }
    
    try {
      setIsSummarizing(true);
      const response = await fetch(`${API}/process-text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: textTitle,
          content: textContent,
          content_type: contentType
        })
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to process content');
      }
      
      const data = await response.json();
      setSummarizedData(data);
      
      // Set extracted data for consistency
      setExtractedData({
        title: textTitle,
        snippet: textContent,
        url: null
      });
    } catch (error) {
      console.error('Error processing text:', error);
      alert(`Error processing content: ${error.message}`);
    } finally {
      setIsSummarizing(false);
    }
  };

  const processImageContent = async () => {
    if (!imageFile || !imageTitle.trim()) {
      alert('Please select an image and enter a title');
      return;
    }
    
    try {
      setIsSummarizing(true);
      
      // Convert image to base64
      const reader = new FileReader();
      reader.onload = async (e) => {
        const base64Data = e.target.result;
        
        try {
          const response = await fetch(`${API}/process-image`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              title: imageTitle,
              image_data: base64Data,
              description: imageDescription,
              content_type: 'image'
            })
          });
          
          if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to process image');
          }
          
          const data = await response.json();
          setSummarizedData(data);
          
          // Set extracted data for consistency
          setExtractedData({
            title: imageTitle,
            snippet: imageDescription || 'Image content',
            url: null,
            imageData: base64Data
          });
        } catch (error) {
          console.error('Error processing image:', error);
          alert(`Error processing image: ${error.message}`);
        } finally {
          setIsSummarizing(false);
        }
      };
      
      reader.readAsDataURL(imageFile);
    } catch (error) {
      console.error('Error reading image:', error);
      alert(`Error reading image: ${error.message}`);
      setIsSummarizing(false);
    }
  };

  const summarizeContent = async (data = extractedData) => {
    if (!data) return;
    
    try {
      setIsSummarizing(true);
      const response = await fetch(`${API}/summarize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          snippet: data.snippet,
          url: data.url,
          title: data.title,
          content_type: 'web_snippet'
        })
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to summarize snippet');
      }
      
      const summaryData = await response.json();
      setSummarizedData(summaryData);
    } catch (error) {
      console.error('Error summarizing snippet:', error);
      alert(`Error summarizing snippet: ${error.message}`);
    } finally {
      setIsSummarizing(false);
    }
  };

  const saveToIrysBlockchain = async () => {
    if (!extractedData || !summarizedData || !irysUploader || !userAddress) return;
    
    try {
      setIsSaving(true);
      
      // Prepare content data for Irys blockchain storage
      const blockchainData = {
        applicationId: "IrysSnippetVault",
        user: userAddress,
        contentType: contentType,
        url: extractedData.url,
        title: extractedData.title,
        content: contentType === 'image' ? extractedData.imageData : extractedData.snippet,
        summary: summarizedData.summary,
        tags: summarizedData.tags,
        mood: summarizedData.mood,
        theme: summarizedData.theme,
        timestamp: Date.now(),
        network: network
      };
      
      // Upload to REAL Irys blockchain via our backend
      const receipt = await irysUploader.upload(JSON.stringify(blockchainData), {
        tags: [
          { name: "application-id", value: "IrysSnippetVault" },
          { name: "user", value: userAddress },
          { name: "content-type", value: contentType },
          { name: "title", value: extractedData.title },
          { name: "Content-Type", value: "application/json" },
          ...summarizedData.tags.map(tag => ({ name: "tag", value: tag }))
        ]
      });
      
      // Save metadata to database for social features
      try {
        await fetch(`${API}/save-snippet-metadata`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            wallet_address: userAddress,
            irys_id: receipt.id,
            url: extractedData.url,
            title: extractedData.title,
            summary: summarizedData.summary,
            tags: summarizedData.tags,
            network: network,
            content_type: contentType,
            mood: summarizedData.mood,
            theme: summarizedData.theme,
            is_public: true
          })
        });
      } catch (metadataError) {
        console.error('Error saving metadata:', metadataError);
      }
      
      const gatewayUrl = network === 'devnet' 
        ? `https://devnet.irys.xyz/${receipt.id}`
        : `https://gateway.irys.xyz/${receipt.id}`;
      
      const contentTypeLabel = contentTypes.find(ct => ct.id === contentType)?.label || contentType;
      alert(`🎉 SUCCESS! ${contentTypeLabel} saved to Irys blockchain!\n\nTransaction ID: ${receipt.id}\n\nView permanently stored data:\n${gatewayUrl}\n\nThis is now stored FOREVER on the blockchain!`);
      
      resetForm();
      if (onSnippetSaved) onSnippetSaved();
      
    } catch (error) {
      console.error('Error saving to Irys blockchain:', error);
      alert(`Error saving to blockchain: ${error.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  const renderContentTypeSelector = () => (
    <div className="content-type-selector">
      <h3>Choose Content Type</h3>
      <div className="content-type-tabs">
        {contentTypes.map((type) => (
          <button
            key={type.id}
            onClick={() => handleContentTypeChange(type.id)}
            className={`content-type-tab ${contentType === type.id ? 'active' : ''}`}
          >
            <span className="tab-icon">{type.icon}</span>
            <div className="tab-content">
              <span className="tab-label">{type.label}</span>
              <span className="tab-description">{type.description}</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );

  const renderContentInput = () => {
    switch (contentType) {
      case 'web_snippet':
        return (
          <div className="form-group">
            <label htmlFor="url">Website URL</label>
            <input
              id="url"
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/article"
              className="url-input"
            />
            <NeonButton 
              onClick={extractSnippet} 
              disabled={!url.trim() || isExtracting}
              className="extract-button"
            >
              {isExtracting ? <LoadingSpinner size="sm" /> : "Extract Snippet"}
            </NeonButton>
          </div>
        );
      
      case 'text':
      case 'poetry':
        return (
          <div className="form-group">
            <label htmlFor="textTitle">Title</label>
            <input
              id="textTitle"
              type="text"
              value={textTitle}
              onChange={(e) => setTextTitle(e.target.value)}
              placeholder="Enter title for your content"
              className="text-input"
            />
            <label htmlFor="textContent">Content</label>
            <textarea
              id="textContent"
              value={textContent}
              onChange={(e) => setTextContent(e.target.value)}
              placeholder="Write your poetry, thoughts, or any text content..."
              className="text-content-input"
              rows="8"
            />
            <NeonButton 
              onClick={processTextContent} 
              disabled={!textContent.trim() || !textTitle.trim() || isSummarizing}
              className="process-button"
            >
              {isSummarizing ? <LoadingSpinner size="sm" /> : "Analyze Content"}
            </NeonButton>
          </div>
        );
      
      case 'image':
        return (
          <div className="form-group">
            <label htmlFor="imageTitle">Image Title</label>
            <input
              id="imageTitle"
              type="text"
              value={imageTitle}
              onChange={(e) => setImageTitle(e.target.value)}
              placeholder="Enter title for your image"
              className="text-input"
            />
            <label htmlFor="imageFile">Upload Image</label>
            <input
              id="imageFile"
              type="file"
              accept="image/*"
              onChange={(e) => setImageFile(e.target.files[0])}
              className="file-input"
            />
            <label htmlFor="imageDescription">Description (Optional)</label>
            <textarea
              id="imageDescription"
              value={imageDescription}
              onChange={(e) => setImageDescription(e.target.value)}
              placeholder="Describe your image..."
              className="text-content-input"
              rows="3"
            />
            <NeonButton 
              onClick={processImageContent} 
              disabled={!imageFile || !imageTitle.trim() || isSummarizing}
              className="process-button"
            >
              {isSummarizing ? <LoadingSpinner size="sm" /> : "Process Image"}
            </NeonButton>
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <GlassCard className="snippet-form">
      <h2 className="form-title">✨ Create Content for Irys Blockchain</h2>
      
      {renderContentTypeSelector()}
      
      {renderContentInput()}

      {extractedData && (
        <div className="extracted-content">
          <h3>📄 {contentType === 'image' ? 'Image' : 'Content'} Preview</h3>
          <div className="content-preview">
            <h4>{extractedData.title}</h4>
            {extractedData.imageData ? (
              <div className="image-preview">
                <img src={extractedData.imageData} alt={extractedData.title} className="preview-image" />
                <p className="snippet-text">{extractedData.snippet}</p>
              </div>
            ) : (
              <p className="snippet-text">{extractedData.snippet}</p>
            )}
          </div>
        </div>
      )}

      {isSummarizing && (
        <div className="summarizing">
          <LoadingSpinner size="md" />
          <p>AI is analyzing your {contentTypes.find(ct => ct.id === contentType)?.label.toLowerCase()}...</p>
        </div>
      )}

      {summarizedData && (
        <div className="summarized-content">
          <h3>🤖 AI Analysis Complete</h3>
          <div className="summary-section">
            <h4>Summary</h4>
            <p>{summarizedData.summary}</p>
          </div>
          <div className="tags-section">
            <h4>Tags</h4>
            <div className="tags-container">
              {summarizedData.tags.map((tag, index) => (
                <span key={index} className="tag">{tag}</span>
              ))}
            </div>
          </div>
          {summarizedData.mood && (
            <div className="mood-section">
              <h4>Mood</h4>
              <span className="mood-badge">{summarizedData.mood}</span>
            </div>
          )}
          {summarizedData.theme && (
            <div className="theme-section">
              <h4>Theme</h4>
              <span className="theme-badge">{summarizedData.theme}</span>
            </div>
          )}
        </div>
      )}

      {extractedData && summarizedData && (
        <div className="save-section">
          <div className="blockchain-info">
            <h3>⛓️ Ready for Irys Blockchain Storage</h3>
            <div className="network-info">
              <p className="info-text">
                <strong>Content Type:</strong> {contentTypes.find(ct => ct.id === contentType)?.label}<br/>
                <strong>Network:</strong> Irys {network === 'devnet' ? 'Devnet (Free Testing)' : 'Mainnet (Production)'}<br/>
                <strong>Storage:</strong> Permanent & Immutable<br/>
                <strong>Cost:</strong> <span className="free-badge">{network === 'devnet' ? 'FREE' : 'Small ETH fee'}</span>
              </p>
            </div>
          </div>
          
          <div className="network-selector">
            <label>Choose Irys Network:</label>
            <div className="radio-group">
              <label className="radio-label">
                <input
                  type="radio"
                  value="devnet"
                  checked={network === 'devnet'}
                  onChange={(e) => setNetwork(e.target.value)}
                />
                <div className="network-option">
                  <strong>Devnet</strong> (devnet.irys.xyz)
                  <br/>
                  <small>Free • Testing • Same permanence</small>
                </div>
              </label>
              <label className="radio-label">
                <input
                  type="radio"
                  value="mainnet"
                  checked={network === 'mainnet'}
                  onChange={(e) => setNetwork(e.target.value)}
                />
                <div className="network-option">
                  <strong>Mainnet</strong> (gateway.irys.xyz)
                  <br/>
                  <small>Paid • Production • Real ETH cost</small>
                </div>
              </label>
            </div>
          </div>
          
          <NeonButton 
            onClick={saveToIrysBlockchain} 
            disabled={isSaving || !irysUploader}
            className="save-button"
          >
            {isSaving ? <LoadingSpinner size="sm" /> : `💾 Save to Irys ${network === 'devnet' ? 'Devnet' : 'Mainnet'} (${network === 'devnet' ? 'FREE' : 'Paid'})`}
          </NeonButton>
        </div>
      )}
    </GlassCard>
  );
};

// Snippet List Component - Now fetches from REAL Irys blockchain
const SnippetList = ({ userAddress, refreshTrigger }) => {
  const [snippets, setSnippets] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchSnippets = async () => {
    if (!userAddress) return;
    
    try {
      setIsLoading(true);
      // Fetch from backend which queries real Irys blockchain
      const response = await fetch(`${API}/irys-query/${userAddress}`);
      const data = await response.json();
      setSnippets(data.snippets || []);
    } catch (error) {
      console.error('Error fetching snippets from blockchain:', error);
      setSnippets([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSnippets();
  }, [userAddress, refreshTrigger]);

  const openUrl = (url) => {
    window.open(url, '_blank');
  };

  const openIrysGateway = (irysId) => {
    window.open(`https://gateway.irys.xyz/${irysId}`, '_blank');
  };

  if (isLoading) {
    return (
      <GlassCard className="snippet-list">
        <div className="loading-container">
          <LoadingSpinner size="lg" />
          <p>Loading your snippets from Irys blockchain...</p>
        </div>
      </GlassCard>
    );
  }

  return (
    <GlassCard className="snippet-list">
      <h2 className="list-title">🔗 Your Blockchain Snippet Vault</h2>
      
      {snippets.length === 0 ? (
        <div className="empty-state">
          <p>No snippets found on the blockchain yet.</p>
          <p className="small-text">Save your first snippet to start building your permanent collection!</p>
        </div>
      ) : (
        <div className="snippets-grid">
          {snippets.map((snippet) => (
            <div key={snippet.id} className="snippet-card">
              <div className="snippet-header">
                <h3>{snippet.title}</h3>
                <span className="network-badge">Irys</span>
              </div>
              <p className="snippet-summary">{snippet.summary}</p>
              <div className="snippet-tags">
                {snippet.tags && snippet.tags.map((tag, index) => (
                  <span key={index} className="tag">{tag}</span>
                ))}
              </div>
              <div className="snippet-footer">
                <button 
                  onClick={() => openUrl(snippet.url)}
                  className="original-link"
                >
                  📄 Original
                </button>
                <button 
                  onClick={() => openIrysGateway(snippet.irys_id)}
                  className="irys-link"
                >
                  🔗 Blockchain
                </button>
              </div>
              <div className="blockchain-info">
                <span className="tx-id">TX: {snippet.irys_id?.slice(0, 8)}...{snippet.irys_id?.slice(-6)}</span>
                <span className="permanent-badge">PERMANENT</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </GlassCard>
  );
};

// Main App Component
function App() {
  const [signer, setSigner] = useState(null);
  const [userAddress, setUserAddress] = useState(null);
  const [balance, setBalance] = useState(null);
  const [refreshSnippets, setRefreshSnippets] = useState(0);
  const [currentTab, setCurrentTab] = useState('home');

  const handleWalletConnected = async (connectedSigner, address) => {
    setSigner(connectedSigner);
    setUserAddress(address);
    
    // Get wallet balance
    try {
      const provider = new ethers.BrowserProvider(window.ethereum);
      const bal = await provider.getBalance(address);
      setBalance(ethers.formatEther(bal));
    } catch (error) {
      console.error('Error getting balance:', error);
    }
  };

  const handleSnippetSaved = () => {
    setRefreshSnippets(prev => prev + 1);
  };

  const renderCurrentTab = () => {
    if (!signer) {
      return (
        <div className="welcome-screen">
          <GlassCard className="welcome-card">
            <h2>Welcome to Irys Snippet Vault</h2>
            <p>Connect your wallet to start saving web snippets permanently on Irys blockchain.</p>
            <ul className="features-list">
              <li>🔗 Extract content from any webpage</li>
              <li>🤖 AI-powered summarization and tagging</li>
              <li>⛓️ <strong>REAL</strong> permanent storage on Irys blockchain</li>
              <li>🎨 Beautiful Notion-style interface</li>
              <li>👥 Social features - follow users, like snippets, comment</li>
              <li>🌐 Public feed to discover trending content</li>
            </ul>
            <div className="demo-section">
              <h3>🔥 Real Irys Blockchain Storage</h3>
              <p>Your snippets will be <strong>permanently stored</strong> on Irys blockchain forever!</p>
              <div className="network-comparison">
                <div className="network-card devnet">
                  <h4>🆓 Devnet (Recommended)</h4>
                  <ul>
                    <li>✅ <strong>FREE</strong> to use</li>
                    <li>✅ Same permanence as mainnet</li>
                    <li>✅ Perfect for testing</li>
                    <li>🌐 Access: devnet.irys.xyz</li>
                  </ul>
                </div>
                <div className="network-card mainnet">
                  <h4>💰 Mainnet (Production)</h4>
                  <ul>
                    <li>💸 Small ETH fees</li>
                    <li>✅ Production network</li>
                    <li>✅ Same features</li>
                    <li>🌐 Access: gateway.irys.xyz</li>
                  </ul>
                </div>
              </div>
              <p className="small-text">
                💡 <strong>Both networks store data permanently!</strong> Devnet is free and perfect for trying the app.
              </p>
            </div>
          </GlassCard>
        </div>
      );
    }

    switch (currentTab) {
      case 'home':
        return (
          <div className="tab-content">
            <SnippetForm 
              signer={signer}
              userAddress={userAddress}
              onSnippetSaved={handleSnippetSaved}
            />
            <SnippetList 
              userAddress={userAddress}
              refreshTrigger={refreshSnippets}
            />
          </div>
        );
      case 'feed':
        return (
          <div className="tab-content">
            <PublicFeed userAddress={userAddress} />
          </div>
        );
      case 'profile':
        return (
          <div className="tab-content">
            <UserProfile userAddress={userAddress} signer={signer} />
          </div>
        );
      case 'discover':
        return (
          <div className="tab-content">
            <UserDiscovery userAddress={userAddress} />
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="App">
      <div className="app-background">
        <div className="gradient-orb orb-1"></div>
        <div className="gradient-orb orb-2"></div>
        <div className="gradient-orb orb-3"></div>
      </div>
      
      <header className="app-header">
        <div className="header-content">
          <h1 className="app-title">
            <span className="title-icon">🔗</span>
            Irys Snippet Vault
          </h1>
          <p className="app-subtitle">
            Permanently store web snippets on Irys blockchain with AI analysis and social features
          </p>
          <WalletConnection 
            onWalletConnected={handleWalletConnected}
            connectedWallet={userAddress}
            balance={balance}
          />
        </div>
      </header>

      {signer && (
        <Navigation 
          currentTab={currentTab} 
          onTabChange={setCurrentTab}
          userAddress={userAddress}
        />
      )}

      <main className="app-main">
        {renderCurrentTab()}
      </main>
    </div>
  );
}

export default App;