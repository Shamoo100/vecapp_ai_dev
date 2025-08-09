/**
 * VecApp AI Service Route Configuration for API Gateway
 * This file defines all routes that should be registered with the central API gateway
 */

export const vecapp_ai_routes = {
  baseUrl: "/v1/ai",
  routes: [
    // Health and Documentation (Open routes)
    { 
      uri: "/health-check", 
      method: "GET", 
      isOpen: true, 
      permission: [] 
    },
    { 
      uri: "/docs", 
      method: "GET", 
      isOpen: true, 
      permission: [] 
    },
    { 
      uri: "/redoc", 
      method: "GET", 
      isOpen: true, 
      permission: [] 
    },
    { 
      uri: "/openapi.json", 
      method: "GET", 
      isOpen: true, 
      permission: [] 
    },

    // Authentication Context Routes
    {
      uri: "/auth/context",
      method: "GET",
      isOpen: false,
      permission: [],
      authType: "JWT"
    },
    {
      uri: "/auth/user",
      method: "GET",
      isOpen: false,
      permission: [],
      authType: "JWT"
    },
    {
      uri: "/auth/tenant",
      method: "GET",
      isOpen: false,
      permission: [],
      authType: "JWT"
    },
    {
      uri: "/auth/ai-context",
      method: "GET",
      isOpen: false,
      permission: [],
      authType: "JWT"
    },
    {
      uri: "/auth/validate",
      method: "POST",
      isOpen: false,
      permission: [],
      authType: "JWT"
    },
    {
      uri: "/auth/health",
      method: "GET",
      isOpen: true,
      permission: []
    },

    // Example Routes (for testing)
    {
      uri: "/examples/public",
      method: "GET",
      isOpen: true,
      permission: []
    },
    {
      uri: "/examples/optional-auth",
      method: "GET",
      isOpen: false,
      permission: [],
      authType: "JWT"
    },
    {
      uri: "/examples/require-user",
      method: "GET",
      isOpen: false,
      permission: [],
      authType: "JWT"
    },
    {
      uri: "/examples/require-tenant",
      method: "GET",
      isOpen: false,
      permission: [],
      authType: "JWT"
    },
    {
      uri: "/examples/require-both",
      method: "GET",
      isOpen: false,
      permission: [],
      authType: "JWT"
    },
    {
      uri: "/examples/ai-operation",
      method: "GET",
      isOpen: false,
      permission: [],
      authType: "JWT"
    },

    // AI Agent Routes
    {
      uri: "/agents/followup/generate",
      method: "POST",
      isOpen: false,
      permission: ["super_admin", "member_use_ai_followup"],
      authType: "RBAC"
    },
    {
      uri: "/agents/followup/summary",
      method: "POST",
      isOpen: false,
      permission: ["super_admin", "member_use_ai_followup"],
      authType: "RBAC"
    },
    {
      uri: "/agents/data-collection",
      method: "POST",
      isOpen: false,
      permission: ["super_admin", "member_use_ai_data_collection"],
      authType: "RBAC"
    },
    {
      uri: "/agents/specialist",
      method: "POST",
      isOpen: false,
      permission: ["super_admin", "member_use_ai_specialist"],
      authType: "RBAC"
    },

    // Report Generation Routes
    {
      uri: "/reports/generate",
      method: "POST",
      isOpen: false,
      permission: ["super_admin", "member_generate_ai_reports"],
      authType: "RBAC"
    },
    {
      uri: "/reports/{reportId}",
      method: "GET",
      isOpen: false,
      permission: ["super_admin", "member_view_ai_reports"],
      authType: "RBAC"
    },
    {
      uri: "/reports/{reportId}/download",
      method: "GET",
      isOpen: false,
      permission: ["super_admin", "member_view_ai_reports"],
      authType: "RBAC"
    },
    {
      uri: "/reports",
      method: "GET",
      isOpen: false,
      permission: ["super_admin", "member_view_ai_reports"],
      authType: "RBAC"
    },

    // Analytics Routes
    {
      uri: "/analytics/visitor-insights",
      method: "GET",
      isOpen: false,
      permission: ["super_admin", "member_view_ai_analytics"],
      authType: "RBAC"
    },
    {
      uri: "/analytics/member-insights",
      method: "GET",
      isOpen: false,
      permission: ["super_admin", "member_view_ai_analytics"],
      authType: "RBAC"
    },
    {
      uri: "/analytics/trends",
      method: "GET",
      isOpen: false,
      permission: ["super_admin", "member_view_ai_analytics"],
      authType: "RBAC"
    },

    // Feedback Routes
    {
      uri: "/feedback",
      method: "POST",
      isOpen: false,
      permission: [],
      authType: "JWT"
    },
    {
      uri: "/feedback/{feedbackId}",
      method: "GET",
      isOpen: false,
      permission: ["super_admin", "member_view_ai_feedback"],
      authType: "RBAC"
    },

    // Member Service Integration Routes
    {
      uri: "/members/{personId}/profile",
      method: "GET",
      isOpen: false,
      permission: ["super_admin", "member_view_profiles"],
      authType: "RBAC"
    },
    {
      uri: "/members/{personId}/notes",
      method: "GET",
      isOpen: false,
      permission: ["super_admin", "member_view_notes"],
      authType: "RBAC"
    },
    {
      uri: "/members/{personId}/notes",
      method: "POST",
      isOpen: false,
      permission: ["super_admin", "member_create_notes"],
      authType: "RBAC"
    },
    {
      uri: "/members/visitors",
      method: "GET",
      isOpen: false,
      permission: ["super_admin", "member_view_visitors"],
      authType: "RBAC"
    },
    {
      uri: "/members/families/{familyId}",
      method: "GET",
      isOpen: false,
      permission: ["super_admin", "member_view_families"],
      authType: "RBAC"
    },

    // Tenant Management Routes
    {
      uri: "/tenants/provision",
      method: "POST",
      isOpen: false,
      permission: ["super_admin"],
      authType: "RBAC"
    },
    {
      uri: "/tenants/{tenantId}/ai-settings",
      method: "GET",
      isOpen: false,
      permission: ["super_admin", "tenant_admin"],
      authType: "RBAC"
    },
    {
      uri: "/tenants/{tenantId}/ai-settings",
      method: "PATCH",
      isOpen: false,
      permission: ["super_admin", "tenant_admin"],
      authType: "RBAC"
    },

    // AI Service Administration Routes
    {
      uri: "/admin/users",
      method: "GET",
      isOpen: false,
      permission: ["super_admin"],
      authType: "RBAC"
    },
    {
      uri: "/admin/users/sync",
      method: "POST",
      isOpen: false,
      permission: ["super_admin"],
      authType: "RBAC"
    },
    {
      uri: "/admin/ai-usage",
      method: "GET",
      isOpen: false,
      permission: ["super_admin"],
      authType: "RBAC"
    },
    {
      uri: "/admin/ai-usage/export",
      method: "GET",
      isOpen: false,
      permission: ["super_admin"],
      authType: "RBAC"
    }
  ]
};

// AI-specific permissions that should be defined in the central auth system
export const ai_permissions = [
  "member_use_ai_followup",
  "member_use_ai_data_collection", 
  "member_use_ai_specialist",
  "member_generate_ai_reports",
  "member_view_ai_reports",
  "member_view_ai_analytics",
  "member_view_ai_feedback",
  "member_view_profiles",
  "member_view_notes",
  "member_create_notes",
  "member_view_visitors",
  "member_view_families"
];