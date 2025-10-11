# Institutional Components

This directory contains React components for institutional features in MyTaco AI.

## ConsentScreen Component

A modal component that displays data sharing consent information to learners joining an institution.

### Features

- **Clear Data Sharing Information**: Shows exactly what data will and won't be shared
- **Institution & Tutor Details**: Displays assigned tutor and institution information
- **Accept/Decline Actions**: Clear call-to-action buttons with proper loading states
- **Error Handling**: Displays API errors gracefully
- **Mobile Responsive**: Adapts to different screen sizes
- **GDPR Compliant**: Includes rights information and revocation options

### Props

```typescript
interface ConsentScreenProps {
  institutionName: string;    // Name of the institution
  tutorName: string;          // Name of the assigned tutor
  learnerId: string;          // User ID of the learner
  institutionId: string;      // Institution ID
  tutorId: string;            // Tutor ID
  onAccept: () => void;       // Callback when consent is granted
  onDecline: () => void;      // Callback when consent is declined
}
```

### Usage Example

```tsx
import { ConsentScreen } from 'components/institutional/ConsentScreen';

function EnrollmentFlow() {
  const [showConsent, setShowConsent] = useState(true);

  const handleAccept = () => {
    console.log('Consent granted');
    // Navigate to learning dashboard
    setShowConsent(false);
  };

  const handleDecline = () => {
    console.log('Consent declined');
    // Navigate to individual learner path
    setShowConsent(false);
  };

  return showConsent ? (
    <ConsentScreen
      institutionName="Lincoln Academy"
      tutorName="Sarah Johnson"
      learnerId="user123"
      institutionId="inst456"
      tutorId="tutor789"
      onAccept={handleAccept}
      onDecline={handleDecline}
    />
  ) : null;
}
```

### Data Sharing Information

**Will Be Shared:**
- Assessment results (language level, skill scores)
- Learning plans and weekly progress
- Practice session summaries
- Progress metrics (time spent, sessions completed)

**Will NOT Be Shared:**
- Payment information
- Personal messages or notes you create
- Account password
- Email address (unless you share it)

### Styling

The component uses CSS modules with the following key classes:
- `.consent-screen-overlay` - Full-screen overlay
- `.consent-screen-container` - Main modal container
- `.consent-header` - Gradient header section
- `.consent-body` - Main content area
- `.consent-actions` - Button container
- `.btn-accept` / `.btn-decline` - Action buttons

### API Integration

The component automatically calls the consent service when "I Accept" is clicked:

```typescript
await consentService.grantConsent({
  learner_id: learnerId,
  institution_id: institutionId,
  tutor_id: tutorId
});
```

### Error Handling

- API errors are displayed in a red error box
- Accept button shows "Processing..." during API calls
- Buttons are disabled during processing to prevent double-clicks

### Mobile Responsiveness

- Container adapts to full width on mobile
- Buttons stack vertically on small screens
- Touch-friendly button sizes maintained

### Testing

Run Storybook to see different variations:

```bash
npm run storybook
```

Navigate to: **Institutional > ConsentScreen**

Available stories:
- **Default**: Standard consent screen
- **DifferentInstitution**: Different institution/tutor
- **LongInstitutionName**: Long institution name handling

### Dependencies

- React
- TypeScript
- CSS Modules (or regular CSS)
- Axios (for API calls)
- Consent service (automatically imported)

### Future Enhancements

- Localization support for multiple languages
- Customizable data sharing lists per institution
- Consent history/audit trail display
- Bulk consent operations for admins
