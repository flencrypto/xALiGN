/**
 * Global type definitions for Clerk authentication and custom types
 * 
 * This file extends Clerk's default interfaces with custom properties
 * specific to the xALiGN application.
 */

export {}

declare global {
  /**
   * Custom JWT session claims
   * 
   * These claims are added to the session token and can be accessed
   * on both the client and server side.
   * 
   * @example
   * ```tsx
   * const { sessionClaims } = useAuth()
   * console.log(sessionClaims?.metadata.onboardingComplete)
   * ```
   */
  interface CustomJwtSessionClaims {
    /** User's first name */
    firstName?: string
    /** User's primary email address */
    primaryEmail?: string
    /** Application-specific metadata */
    metadata: {
      /** Whether user has completed onboarding */
      onboardingComplete?: boolean
      /** User's organization/company name */
      companyName?: string
      /** User's role in their organization */
      jobTitle?: string
      /** Preferred theme (light/dark) */
      theme?: 'light' | 'dark' | 'system'
      /** Feature flags for the user */
      features?: {
        aiAssist?: boolean
        advancedEstimating?: boolean
        exportPdf?: boolean
      }
    }
  }

  /**
   * Custom authorization configuration for Clerk
   * 
   * Defines custom permissions and roles for organization-based access control.
   * These replace the default org:admin and org:member roles.
   */
  interface ClerkAuthorization {
    /** Custom permissions for bid management */
    permission:
      | 'org:bid:create'
      | 'org:bid:read'
      | 'org:bid:update'
      | 'org:bid:delete'
      | 'org:bid:export'
      | 'org:bid:submit'
      /** Account/opportunity permissions */
      | 'org:account:create'
      | 'org:account:read'
      | 'org:account:update'
      | 'org:account:delete'
      /** Estimating permissions */
      | 'org:estimate:create'
      | 'org:estimate:read'
      | 'org:estimate:update'
      | 'org:estimate:approve'
      /** Framework and intel permissions */
      | 'org:framework:manage'
      | 'org:intel:manage'
      /** Admin permissions */
      | 'org:settings:manage'
      | 'org:members:manage'
      | 'org:billing:manage'

    /** Custom roles for organization members */
    role:
      | 'org:owner'           // Full access to everything
      | 'org:admin'           // Can manage settings and members
      | 'org:bid_manager'     // Can create, edit, and submit bids
      | 'org:estimator'       // Can create and update estimates
      | 'org:viewer'          // Read-only access to bids and accounts
      | 'org:contributor'     // Can create and edit, but not submit/approve
  }

  /**
   * User public metadata
   * 
   * Publicly accessible user data that can be read by anyone in the organization.
   */
  interface UserPublicMetadata {
    /** User's job title */
    jobTitle?: string
    /** User's department */
    department?: string
    /** User's phone number */
    phone?: string
    /** User's avatar color for fallback */
    avatarColor?: string
  }

  /**
   * User private metadata
   * 
   * Private user data that can only be accessed by the user themselves
   * and organization admins.
   */
  interface UserPrivateMetadata {
    /** Internal employee ID */
    employeeId?: string
    /** User's notification preferences */
    notifications?: {
      email?: boolean
      sms?: boolean
      inApp?: boolean
    }
    /** User's timezone */
    timezone?: string
  }

  /**
   * User unsafe metadata
   * 
   * Data that can be set by the user without backend validation.
   * Use with caution - validate on the backend before trusting.
   */
  interface UserUnsafeMetadata {
    /** User's preferred language */
    locale?: string
    /** UI preferences */
    preferences?: {
      sidebarCollapsed?: boolean
      tablePageSize?: number
      dashboardLayout?: string[]
    }
  }

  /**
   * Organization public metadata
   * 
   * Publicly accessible organization data.
   */
  interface OrganizationPublicMetadata {
    /** Organization's industry sector */
    sector?: string
    /** Organization size */
    size?: 'small' | 'medium' | 'large' | 'enterprise'
    /** Organization website */
    website?: string
    /** Organization's subscription plan */
    plan?: 'free' | 'starter' | 'professional' | 'enterprise'
  }

  /**
   * Organization membership metadata
   * 
   * Metadata for organization memberships.
   */
  interface OrganizationMembershipPublicMetadata {
    /** Date when member joined */
    joinedAt?: string
    /** Member's team within the organization */
    team?: string
    /** Member's access level for specific features */
    accessLevel?: {
      bids?: number
      estimates?: number
      exports?: number
    }
  }

  /**
   * Sign-up unsafe metadata
   * 
   * Data collected during sign-up that can be set without backend validation.
   */
  interface SignUpUnsafeMetadata {
    /** How the user heard about the product */
    referralSource?: string
    /** User's initial use case */
    useCase?: string
    /** Company size selection during signup */
    companySize?: string
  }
}
