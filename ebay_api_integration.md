# eBay API Integration Plan

## Overview
Implementing direct eBay API integration will allow the application to create draft listings directly on eBay without the need for CSV exports. This will enable setting many more eBay fields and streamline the workflow.

## Required Components

### 1. eBay Developer Account Setup
- Register for an eBay developer account at [developer.ebay.com](https://developer.ebay.com)
- Create an application to obtain API credentials
- Set up OAuth for user authorization
- Configure redirect URL for authentication flow

### 2. Dependencies
- Add the `ebaysdk` Python package to requirements.txt
- Add `requests_oauthlib` for OAuth handling

### 3. Authentication Flow
- Implement OAuth 2.0 authentication flow
- Store and refresh user tokens securely
- Create routes for authorization and callback

### 4. API Integration
- Implement Trading API calls for creating draft listings
- Map our application fields to eBay API fields
- Handle image uploading to eBay's servers
- Implement error handling and rate limiting

### 5. UI Changes
- Add "Login with eBay" button
- Create a settings page for eBay account management
- Add "Create on eBay" button to listing preview
- Show eBay listing status and link after creation

## Implementation Steps

### Phase 1: Authentication
1. Set up eBay developer account and obtain credentials
2. Implement OAuth login flow
3. Create token storage and refresh mechanism
4. Test authentication with simple API calls

### Phase 2: Basic Listing Creation
1. Implement draft listing creation with minimal fields
2. Add image upload functionality
3. Create UI for direct listing creation
4. Test end-to-end workflow

### Phase 3: Advanced Features
1. Add support for all eBay listing fields
2. Implement listing templates
3. Add bulk listing creation
4. Implement listing management (edit, delete, etc.)

## API Endpoints to Implement

### Authentication
- `/auth/ebay` - Start OAuth flow
- `/auth/ebay/callback` - Handle OAuth callback
- `/auth/ebay/refresh` - Refresh tokens

### Listings
- `/api/ebay/create_draft` - Create draft listing
- `/api/ebay/upload_images` - Upload images to eBay
- `/api/ebay/categories` - Get eBay categories
- `/api/ebay/item_specifics` - Get required item specifics for category

## eBay API Documentation
- [Trading API](https://developer.ebay.com/Devzone/XML/docs/Reference/ebay/index.html)
- [OAuth](https://developer.ebay.com/api-docs/static/oauth-authorization-code-grant.html)
- [Merchant Integration](https://developer.ebay.com/develop/guides/ebay-marketplace-account) 