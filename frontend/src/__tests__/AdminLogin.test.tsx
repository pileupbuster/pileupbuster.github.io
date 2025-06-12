import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import AdminLogin from '../components/AdminLogin';

describe('AdminLogin', () => {
  const mockOnLogin = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders login form correctly', () => {
    render(<AdminLogin onLogin={mockOnLogin} />);
    
    expect(screen.getByText('Admin Login')).toBeInTheDocument();
    expect(screen.getByLabelText('Username')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Login' })).toBeInTheDocument();
  });

  test('disables submit button when fields are empty', () => {
    render(<AdminLogin onLogin={mockOnLogin} />);
    
    const submitButton = screen.getByRole('button', { name: 'Login' });
    expect(submitButton).toBeDisabled();
  });

  test('enables submit button when both fields are filled', () => {
    render(<AdminLogin onLogin={mockOnLogin} />);
    
    const usernameInput = screen.getByLabelText('Username');
    const passwordInput = screen.getByLabelText('Password');
    const submitButton = screen.getByRole('button', { name: 'Login' });
    
    fireEvent.change(usernameInput, { target: { value: 'admin' } });
    fireEvent.change(passwordInput, { target: { value: 'password' } });
    
    expect(submitButton).not.toBeDisabled();
  });

  test('calls onLogin with credentials when form is submitted', () => {
    render(<AdminLogin onLogin={mockOnLogin} />);
    
    const usernameInput = screen.getByLabelText('Username');
    const passwordInput = screen.getByLabelText('Password');
    const submitButton = screen.getByRole('button', { name: 'Login' });
    
    fireEvent.change(usernameInput, { target: { value: 'admin' } });
    fireEvent.change(passwordInput, { target: { value: 'password' } });
    fireEvent.click(submitButton);
    
    expect(mockOnLogin).toHaveBeenCalledWith({
      username: 'admin',
      password: 'password'
    });
  });

  test('shows error message when provided', () => {
    const errorMessage = 'Invalid credentials';
    render(<AdminLogin onLogin={mockOnLogin} error={errorMessage} />);
    
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  test('shows loading state when isLoading is true', () => {
    render(<AdminLogin onLogin={mockOnLogin} isLoading={true} />);
    
    expect(screen.getByText('Logging in...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /logging in/i })).toBeDisabled();
  });

  test('disables form inputs when loading', () => {
    render(<AdminLogin onLogin={mockOnLogin} isLoading={true} />);
    
    const usernameInput = screen.getByLabelText('Username');
    const passwordInput = screen.getByLabelText('Password');
    
    expect(usernameInput).toBeDisabled();
    expect(passwordInput).toBeDisabled();
  });

  test('does not call onLogin when form is submitted with empty fields', () => {
    render(<AdminLogin onLogin={mockOnLogin} />);
    
    const form = screen.getByRole('button', { name: 'Login' }).closest('form');
    fireEvent.submit(form!);
    
    expect(mockOnLogin).not.toHaveBeenCalled();
  });
});