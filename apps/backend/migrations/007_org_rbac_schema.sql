-- Migration 007: Organization RBAC Schema
-- Date: 2026-03-22
-- Description: Create organization and role-based access control tables for multi-tenant architecture

-- Table: organizations
-- Represents organizations/companies that own resources and have users
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    domain VARCHAR(255),
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Indexes for organizations
CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organizations_owner_id ON organizations(owner_id);
CREATE INDEX idx_organizations_is_active ON organizations(is_active);
CREATE INDEX idx_organizations_created_at ON organizations(created_at);

-- Table: org_members
-- Maps users to organizations with role and status
CREATE TABLE IF NOT EXISTS org_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    invited_by UUID REFERENCES users(id) ON DELETE SET NULL,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(org_id, user_id)
);

-- Indexes for org_members
CREATE INDEX idx_org_members_org_id ON org_members(org_id);
CREATE INDEX idx_org_members_user_id ON org_members(user_id);
CREATE INDEX idx_org_members_role ON org_members(role);
CREATE INDEX idx_org_members_status ON org_members(status);
CREATE INDEX idx_org_members_joined_at ON org_members(joined_at);

-- Table: org_invitations
-- Manages pending invitations to join organizations
CREATE TABLE IF NOT EXISTS org_invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    invited_by UUID REFERENCES users(id) ON DELETE SET NULL,
    accepted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Indexes for org_invitations
CREATE INDEX idx_org_invitations_org_id ON org_invitations(org_id);
CREATE INDEX idx_org_invitations_email ON org_invitations(email);
CREATE INDEX idx_org_invitations_token ON org_invitations(token);
CREATE INDEX idx_org_invitations_status ON org_invitations(status);
CREATE INDEX idx_org_invitations_expires_at ON org_invitations(expires_at);

-- Table: org_roles
-- Custom roles with permissions for organizations
CREATE TABLE IF NOT EXISTS org_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    permissions JSONB NOT NULL DEFAULT '[]',
    is_system_role BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(org_id, name)
);

-- Indexes for org_roles
CREATE INDEX idx_org_roles_org_id ON org_roles(org_id);
CREATE INDEX idx_org_roles_name ON org_roles(name);
CREATE INDEX idx_org_roles_is_system_role ON org_roles(is_system_role);

-- Add organization fields to users table if not present
ALTER TABLE users
ADD COLUMN IF NOT EXISTS primary_org_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS org_id UUID REFERENCES organizations(id) ON DELETE SET NULL;

-- Create indexes for user organization fields
CREATE INDEX IF NOT EXISTS idx_users_primary_org_id ON users(primary_org_id);
CREATE INDEX IF NOT EXISTS idx_users_org_id ON users(org_id);

-- Add audit logging for organization changes
CREATE TABLE IF NOT EXISTS org_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    changes JSONB DEFAULT '{}',
    ip_address VARCHAR(45),
    user_agent TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'success',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Indexes for org_audit_logs
CREATE INDEX idx_org_audit_logs_org_id ON org_audit_logs(org_id);
CREATE INDEX idx_org_audit_logs_user_id ON org_audit_logs(user_id);
CREATE INDEX idx_org_audit_logs_action ON org_audit_logs(action);
CREATE INDEX idx_org_audit_logs_created_at ON org_audit_logs(created_at);

-- Add comments for documentation
COMMENT ON TABLE organizations IS 'Represents organizations/companies in the system';
COMMENT ON TABLE org_members IS 'Maps users to organizations with role and status';
COMMENT ON TABLE org_invitations IS 'Pending invitations for users to join organizations';
COMMENT ON TABLE org_roles IS 'Custom roles with permissions for organizations';
COMMENT ON TABLE org_audit_logs IS 'Audit trail for organization-level changes';
