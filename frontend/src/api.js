import axios from 'axios'

export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost'

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  withCredentials: true,
})

export function getApiErrorMessage(error, fallbackMessage) {
  return error?.response?.data?.error || fallbackMessage
}
