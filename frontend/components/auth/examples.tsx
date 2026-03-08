/**
 * Example components demonstrating Clerk authentication patterns with custom types
 * 
 * This file shows practical examples of:
 * - Using custom JWT claims
 * - Checking permissions and roles
 * - Accessing user metadata
 * - Protecting UI elements based on auth state
 */

'use client'

import { useAuth, useUser } from '@clerk/nextjs'

/**
 * Example 1: Display user profile with custom metadata
 */
export function UserProfileCard() {
  const { user } = useUser()
  const { sessionClaims } = useAuth()

  if (!user) {
    return <div>Not authenticated</div>
  }

  // Access custom JWT claims (defined in types/globals.d.ts)
  const onboardingComplete = sessionClaims?.metadata.onboardingComplete
  const companyName = sessionClaims?.metadata.companyName
  const jobTitle = sessionClaims?.metadata.jobTitle
  const theme = sessionClaims?.metadata.theme || 'system'

  // Access user public metadata
  const userJobTitle = user.publicMetadata?.jobTitle
  const department = user.publicMetadata?.department

  return (
    <div className="rounded-lg border p-6">
      <div className="flex items-center gap-4">
        <img 
          src={user.imageUrl} 
          alt={user.fullName || 'User'} 
          className="h-16 w-16 rounded-full"
        />
        <div>
          <h2 className="text-xl font-bold">{user.fullName}</h2>
          <p className="text-sm text-muted-foreground">
            {user.primaryEmailAddress?.emailAddress}
          </p>
          {(userJobTitle || jobTitle) && (
            <p className="text-sm">{userJobTitle || jobTitle}</p>
          )}
          {companyName && (
            <p className="text-sm text-muted-foreground">{companyName}</p>
          )}
        </div>
      </div>

      {!onboardingComplete && (
        <div className="mt-4 rounded-md bg-yellow-50 p-3 text-sm text-yellow-800">
          ⚠️ Please complete your onboarding
        </div>
      )}

      <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
        <div>
          <span className="font-medium">Department:</span> {department || 'Not set'}
        </div>
        <div>
          <span className="font-medium">Theme:</span> {theme}
        </div>
      </div>
    </div>
  )
}

/**
 * Example 2: Bid action buttons with permission checks
 */
export function BidActionButtons({ bidId }: { bidId: string }) {
  const { has, isLoaded } = useAuth()

  if (!isLoaded) {
    return <div>Loading permissions...</div>
  }

  return (
    <div className="flex gap-2">
      {/* Only show if user has bid read permission */}
      {has({ permission: 'org:bid:read' }) && (
        <button className="btn btn-secondary">
          View Bid
        </button>
      )}

      {/* Only show if user has bid update permission */}
      {has({ permission: 'org:bid:update' }) && (
        <button className="btn btn-primary">
          Edit Bid
        </button>
      )}

      {/* Only show if user has bid submit permission */}
      {has({ permission: 'org:bid:submit' }) && (
        <button className="btn btn-success">
          Submit Bid
        </button>
      )}

      {/* Only show if user has bid delete permission */}
      {has({ permission: 'org:bid:delete' }) && (
        <button className="btn btn-danger">
          Delete Bid
        </button>
      )}

      {/* Only show if user has bid export permission */}
      {has({ permission: 'org:bid:export' }) && (
        <button className="btn btn-secondary">
          Export PDF
        </button>
      )}
    </div>
  )
}

/**
 * Example 3: Role-based UI sections
 */
export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { has, isLoaded } = useAuth()

  if (!isLoaded) {
    return <div>Loading...</div>
  }

  return (
    <div className="grid grid-cols-12 gap-6">
      {/* Main content - visible to all authenticated users */}
      <div className="col-span-12 lg:col-span-9">
        {children}
      </div>

      {/* Sidebar with role-based sections */}
      <aside className="col-span-12 lg:col-span-3">
        {/* Admin panel - only for admins and owners */}
        {(has({ role: 'org:admin' }) || has({ role: 'org:owner' })) && (
          <div className="mb-6 rounded-lg border p-4">
            <h3 className="mb-3 font-semibold">Admin Panel</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="/dashboard/settings">⚙️ Settings</a>
              </li>
              <li>
                <a href="/dashboard/members">👥 Manage Members</a>
              </li>
              {has({ permission: 'org:billing:manage' }) && (
                <li>
                  <a href="/dashboard/billing">💳 Billing</a>
                </li>
              )}
            </ul>
          </div>
        )}

        {/* Bid Manager tools */}
        {has({ role: 'org:bid_manager' }) && (
          <div className="mb-6 rounded-lg border p-4">
            <h3 className="mb-3 font-semibold">Bid Manager Tools</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="/dashboard/bids/pending">📋 Pending Approvals</a>
              </li>
              <li>
                <a href="/dashboard/bids/submitted">✅ Submitted Bids</a>
              </li>
              <li>
                <a href="/dashboard/templates">📄 Templates</a>
              </li>
            </ul>
          </div>
        )}

        {/* Estimator tools */}
        {has({ role: 'org:estimator' }) && (
          <div className="mb-6 rounded-lg border p-4">
            <h3 className="mb-3 font-semibold">Estimator Tools</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="/dashboard/estimating">🧮 My Estimates</a>
              </li>
              <li>
                <a href="/dashboard/lead-times">⏱️ Lead Times</a>
              </li>
              <li>
                <a href="/dashboard/frameworks">📚 Frameworks</a>
              </li>
            </ul>
          </div>
        )}

        {/* Viewer notice */}
        {has({ role: 'org:viewer' }) && (
          <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
            <p className="text-sm text-blue-800">
              ℹ️ You have view-only access. Contact your admin to request
              additional permissions.
            </p>
          </div>
        )}
      </aside>
    </div>
  )
}

/**
 * Example 4: Feature flag checks from custom JWT claims
 */
export function AIAssistButton() {
  const { sessionClaims } = useAuth()

  // Check if AI assist feature is enabled for this user
  const aiAssistEnabled = sessionClaims?.metadata.features?.aiAssist

  if (!aiAssistEnabled) {
    return (
      <button disabled className="btn btn-secondary opacity-50">
        🤖 AI Assist (Upgrade to enable)
      </button>
    )
  }

  return (
    <button className="btn btn-primary">
      🤖 AI Assist
    </button>
  )
}

/**
 * Example 5: Onboarding check
 */
export function OnboardingGate({ children }: { children: React.ReactNode }) {
  const { sessionClaims } = useAuth()
  const onboardingComplete = sessionClaims?.metadata.onboardingComplete

  if (!onboardingComplete) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="max-w-md text-center">
          <h1 className="mb-4 text-2xl font-bold">Welcome to xALiGN!</h1>
          <p className="mb-6 text-muted-foreground">
            Let's get you set up with a few quick questions.
          </p>
          <button className="btn btn-primary">
            Start Onboarding
          </button>
        </div>
      </div>
    )
  }

  return <>{children}</>
}

/**
 * Example 6: Protected server action with permission check
 */
export function CreateBidButton() {
  const { has, userId } = useAuth()

  async function handleCreateBid() {
    try {
      // Permission check on client side
      if (!has({ permission: 'org:bid:create' })) {
        alert('You do not have permission to create bids')
        return
      }

      // Call API - backend will also verify permissions
      const response = await fetch('/api/v1/bids', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: 'New Bid',
          created_by: userId,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to create bid')
      }

      const bid = await response.json()
      console.log('Created bid:', bid)
      
      // Redirect to bid page
      window.location.href = `/dashboard/bids/${bid.id}`
    } catch (error) {
      console.error('Error creating bid:', error)
      alert('Failed to create bid. Please try again.')
    }
  }

  // Don't show button if user doesn't have permission
  if (!has({ permission: 'org:bid:create' })) {
    return null
  }

  return (
    <button 
      onClick={handleCreateBid}
      className="btn btn-primary"
    >
      ➕ Create New Bid
    </button>
  )
}

/**
 * Example 7: Update user metadata
 */
export function ThemeSelector() {
  const { user } = useUser()
  const { sessionClaims } = useAuth()

  const currentTheme = sessionClaims?.metadata.theme || 'system'

  async function updateTheme(theme: 'light' | 'dark' | 'system') {
    try {
      await user?.update({
        unsafeMetadata: {
          ...user.unsafeMetadata,
          theme,
        },
      })

      // Optionally reload to apply theme
      window.location.reload()
    } catch (error) {
      console.error('Error updating theme:', error)
    }
  }

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">Theme Preference</label>
      <div className="flex gap-2">
        <button
          onClick={() => updateTheme('light')}
          className={`btn ${currentTheme === 'light' ? 'btn-primary' : 'btn-secondary'}`}
        >
          ☀️ Light
        </button>
        <button
          onClick={() => updateTheme('dark')}
          className={`btn ${currentTheme === 'dark' ? 'btn-primary' : 'btn-secondary'}`}
        >
          🌙 Dark
        </button>
        <button
          onClick={() => updateTheme('system')}
          className={`btn ${currentTheme === 'system' ? 'btn-primary' : 'btn-secondary'}`}
        >
          💻 System
        </button>
      </div>
    </div>
  )
}
