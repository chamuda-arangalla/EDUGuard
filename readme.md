# EDUGuard Desktop Application

## Firebase Realtime Database Setup

This application uses Firebase for authentication and the Realtime Database for data storage. Follow these steps to set up Firebase Realtime Database:

1. Go to the [Firebase Console](https://console.firebase.google.com/)
2. Select your project (eduguard-db)
3. In the left sidebar, click on "Build" > "Realtime Database"
4. Click "Create Database" if you haven't created one yet
5. Choose the location closest to your users
6. Start in test mode for development purposes (we'll update the security rules later)

## Security Rules

After setting up the database, update the security rules by going to the "Rules" tab in the Realtime Database section. Use the rules from the `database-rules.json` file provided in this repository. These rules ensure:

- Users can only read and write their own data
- Data structure is properly validated
- Unauthorized access is prevented

```json
{
  "rules": {
    "users": {
      "$uid": {
        ".read": "$uid === auth.uid",
        ".write": "$uid === auth.uid"
        // Additional validation rules...
      }
    },
    "notes": {
      "$uid": {
        ".read": "$uid === auth.uid",
        ".write": "$uid === auth.uid"
        // Additional validation rules...
      }
    }
  }
}
```

## Application Features

### User Profiles
- View and edit your profile information
- Data is stored in the Firebase Realtime Database
- Updates in real-time

### Notes Demo
- Create and delete notes
- Real-time synchronization between devices
- Secure data access

## Getting Started

1. Install dependencies:
   ```
   cd frontend
   npm install
   ```

2. Start the development server:
   ```
   npm run dev
   ```

3. Access the application features:
   - Register a new user or log in
   - Navigate to the Profile page to update your information
   - Try the Database Test page to experiment with the notes functionality

## Data Structure

The application uses the following data structure in Firebase:

```
- users
  - $userId
    - displayName: string
    - bio: string
    - phone: string

- notes
  - $userId
    - $noteId
      - text: string
      - createdAt: number
```

## API Reference

The application provides a set of utility functions for interacting with the database:

- `createData(path, data)`: Create data at a specific path
- `createDataWithId(path, data)`: Create data with an auto-generated ID
- `readData(path)`: Read data from a specific path
- `subscribeToData(path, callback)`: Subscribe to real-time updates
- `updateData(path, data)`: Update data at a specific path
- `deleteData(path)`: Delete data at a specific path
- `queryData(path, child, value)`: Query data based on specific criteria 