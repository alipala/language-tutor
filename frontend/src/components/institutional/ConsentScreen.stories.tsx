import React from 'react';
import { Meta, StoryFn } from '@storybook/react';
import { ConsentScreen } from './ConsentScreen';

export default {
  title: 'Institutional/ConsentScreen',
  component: ConsentScreen,
  parameters: {
    layout: 'fullscreen',
  },
} as Meta<typeof ConsentScreen>;

const Template: StoryFn<typeof ConsentScreen> = (args) => <ConsentScreen {...args} />;

export const Default = Template.bind({});
Default.args = {
  institutionName: 'Lincoln Academy',
  tutorName: 'Sarah Johnson',
  learnerId: 'user123',
  institutionId: 'inst456',
  tutorId: 'tutor789',
  onAccept: () => console.log('Consent granted'),
  onDecline: () => console.log('Consent declined'),
};

export const DifferentInstitution = Template.bind({});
DifferentInstitution.args = {
  institutionName: 'Global Language Institute',
  tutorName: 'Maria Lopez',
  learnerId: 'user456',
  institutionId: 'inst789',
  tutorId: 'tutor012',
  onAccept: () => console.log('Consent granted'),
  onDecline: () => console.log('Consent declined'),
};

export const LongInstitutionName = Template.bind({});
LongInstitutionName.args = {
  institutionName: 'The International Center for Language Excellence and Cultural Studies',
  tutorName: 'Dr. Michael Chen',
  learnerId: 'user789',
  institutionId: 'inst101',
  tutorId: 'tutor345',
  onAccept: () => console.log('Consent granted'),
  onDecline: () => console.log('Consent declined'),
};
