import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import CallsignForm from '../components/CallsignForm';
import { queueApi } from '../services/api';

// Mock the API
jest.mock('../services/api');
const mockedQueueApi = queueApi as jest.Mocked<typeof queueApi>;

describe('CallsignForm', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders form elements correctly', () => {
    render(<CallsignForm />);
    
    expect(screen.getByText('Register Your Callsign')).toBeInTheDocument();
    expect(screen.getByLabelText('Callsign')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Register Callsign' })).toBeInTheDocument();
  });

  test('converts callsign to uppercase', () => {
    render(<CallsignForm />);
    
    const input = screen.getByLabelText('Callsign');
    fireEvent.change(input, { target: { value: 'w1aw' } });
    
    expect(input).toHaveValue('W1AW');
  });

  test('disables submit button when callsign is empty', () => {
    render(<CallsignForm />);
    
    const submitButton = screen.getByRole('button', { name: 'Register Callsign' });
    expect(submitButton).toBeDisabled();
  });

  test('enables submit button when callsign is entered', () => {
    render(<CallsignForm />);
    
    const input = screen.getByLabelText('Callsign');
    const submitButton = screen.getByRole('button', { name: 'Register Callsign' });
    
    fireEvent.change(input, { target: { value: 'W1AW' } });
    expect(submitButton).not.toBeDisabled();
  });

  test('shows error message for empty callsign submission', async () => {
    render(<CallsignForm />);
    
    const form = screen.getByRole('button', { name: 'Register Callsign' }).closest('form');
    
    // Submit the form directly to bypass button disabled state
    fireEvent.submit(form!);
    
    await waitFor(() => {
      expect(screen.getByText('Please enter a callsign')).toBeInTheDocument();
    });
  });

  test('calls onSuccess callback when registration succeeds', async () => {
    const mockOnSuccess = jest.fn();
    const mockResponse = {
      message: 'Success',
      entry: { callsign: 'W1AW', position: 1, timestamp: '2023-01-01T00:00:00Z' }
    };
    
    mockedQueueApi.register.mockResolvedValueOnce(mockResponse);
    
    render(<CallsignForm onSuccess={mockOnSuccess} />);
    
    const input = screen.getByLabelText('Callsign');
    const submitButton = screen.getByRole('button', { name: 'Register Callsign' });
    
    fireEvent.change(input, { target: { value: 'W1AW' } });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockOnSuccess).toHaveBeenCalledWith('W1AW', 1);
    });
    
    expect(input).toHaveValue(''); // Form should be cleared
  });

  test('shows error message when registration fails', async () => {
    const mockError = new Error('Registration failed');
    mockedQueueApi.register.mockRejectedValueOnce(mockError);
    
    render(<CallsignForm />);
    
    const input = screen.getByLabelText('Callsign');
    const submitButton = screen.getByRole('button', { name: 'Register Callsign' });
    
    fireEvent.change(input, { target: { value: 'W1AW' } });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Registration failed')).toBeInTheDocument();
    });
  });

  test('shows loading state during submission', async () => {
    let resolvePromise: (value: any) => void;
    const mockPromise = new Promise((resolve) => {
      resolvePromise = resolve;
    });
    
    mockedQueueApi.register.mockReturnValueOnce(mockPromise);
    
    render(<CallsignForm />);
    
    const input = screen.getByLabelText('Callsign');
    const submitButton = screen.getByRole('button', { name: 'Register Callsign' });
    
    fireEvent.change(input, { target: { value: 'W1AW' } });
    fireEvent.click(submitButton);
    
    expect(screen.getByText('Registering...')).toBeInTheDocument();
    expect(submitButton).toBeDisabled();
    
    // Resolve the promise
    resolvePromise!({
      message: 'Success',
      entry: { callsign: 'W1AW', position: 1, timestamp: '2023-01-01T00:00:00Z' }
    });
    
    await waitFor(() => {
      expect(screen.queryByText('Registering...')).not.toBeInTheDocument();
    });
  });
});