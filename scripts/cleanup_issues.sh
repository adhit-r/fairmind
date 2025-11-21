#!/bin/bash
# Script to clean up GitHub issues - remove emojis and organize

# Emoji mapping for title cleanup
declare -A EMOJI_MAP=(
    ["📱"]="Mobile"
    ["📊"]="Analytics"
    ["🌐"]="Internationalization"
    ["🎨"]="Frontend"
    ["🤖"]="AI/ML"
    ["🎯"]="Performance"
    ["🔒"]="Security"
    ["✨"]="UI/UX"
    ["🧪"]="Testing"
    ["📝"]="Documentation"
    ["🔧"]="Automated"
    ["🗺️"]="Regulatory"
    ["📋"]="Attestation"
    ["🏢"]="Vendor"
    ["🔍"]="Risk"
    ["🔗"]="Data Flow"
    ["🔄"]="Integration"
    ["📈"]="Analytics"
    ["🔐"]="Security"
    ["📚"]="OECD"
    ["🚀"]="Production"
    ["⚖️"]="Advanced"
    ["🔬"]="Advanced"
    ["🛡️"]="Security"
)

# Issues to update (remove emojis)
ISSUES_TO_UPDATE=(
    106 105 104 103 102 101 100 99 98 97
    91 90 89 88 85 84 83 82 80 79 78 77 76 75 74 73 72 71 70 69 68 67
    66 65 64 63 62 61 60 59 58 57 56 55 48
)

# Issues to close (duplicates or invalid)
ISSUES_TO_CLOSE=(
    3  # Set up proper issue tracking workflow - DONE
    4  # Create API endpoints for AI BOM service - Already implemented
    5  # Integrate AI BOM service with database - Already implemented
    6  # Build AI BOM frontend interface - Already implemented
    7  # Add comprehensive testing for AI BOM service - Already implemented
    10 # AI BOM: Frontend interface and dashboard - Already implemented
    11 # AI BOM: External tool integrations - Already implemented
    12 # Model Registry: Core model management system - Already implemented
    13 # Model Registry: Model simulation and testing framework - Already implemented
    14 # Model Registry: Model provenance and lineage tracking - Already implemented
    15 # Fairness Analysis: Advanced bias detection system - Already implemented
    16 # Fairness Analysis: Real-time monitoring and alerting - Already implemented
    18 # Infrastructure: CI/CD pipeline setup - Duplicate of #26
    55 # Production Deployment & Infrastructure Setup - Duplicate of #62
    56 # User Analytics & Performance Monitoring - Similar to #105
    57 # Advanced ML Research & Model Development (Kishore) - Outdated
    58 # ML Pipeline Optimization & Advanced Features (Sanjeev) - Outdated
)

# Issues to add help-wanted tag
ISSUES_NEED_HELP=(
    97 98 99 100 101 102 103 104 105 106
    21 22 23 24 26 27 28 29 30
    62 63 64 65 66
    67 68 69 70 71 72 73
    74 75 76 77 78 79 80 82 83 84 85 88 89 90 91
)

echo "Starting issue cleanup..."

# Function to remove emoji from title
remove_emoji() {
    local title="$1"
    # Remove common emojis
    title=$(echo "$title" | sed 's/📱 *//g')
    title=$(echo "$title" | sed 's/📊 *//g')
    title=$(echo "$title" | sed 's/🌐 *//g')
    title=$(echo "$title" | sed 's/🎨 *//g')
    title=$(echo "$title" | sed 's/🤖 *//g')
    title=$(echo "$title" | sed 's/🎯 *//g')
    title=$(echo "$title" | sed 's/🔒 *//g')
    title=$(echo "$title" | sed 's/✨ *//g')
    title=$(echo "$title" | sed 's/🧪 *//g')
    title=$(echo "$title" | sed 's/📝 *//g')
    title=$(echo "$title" | sed 's/🔧 *//g')
    title=$(echo "$title" | sed 's/🗺️ *//g')
    title=$(echo "$title" | sed 's/📋 *//g')
    title=$(echo "$title" | sed 's/🏢 *//g')
    title=$(echo "$title" | sed 's/🔍 *//g')
    title=$(echo "$title" | sed 's/🔗 *//g')
    title=$(echo "$title" | sed 's/🔄 *//g')
    title=$(echo "$title" | sed 's/📈 *//g')
    title=$(echo "$title" | sed 's/🔐 *//g')
    title=$(echo "$title" | sed 's/📚 *//g')
    title=$(echo "$title" | sed 's/🚀 *//g')
    title=$(echo "$title" | sed 's/⚖️ *//g')
    title=$(echo "$title" | sed 's/🔬 *//g')
    title=$(echo "$title" | sed 's/🛡️ *//g')
    echo "$title"
}

echo "This script will help you clean up issues. Run each command manually for safety."



