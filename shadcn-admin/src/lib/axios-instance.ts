/**
 * Shared axios instance used by Orval-generated API client code.
 *
 * - baseURL '/' so the generated paths (which already include /api/v1/…)
 *   are used verbatim; Vite proxy forwards /api/* to the FastAPI backend.
 * - withCredentials: true forwards the HTTP-only session cookie on every
 *   request so the backend auth middleware can identify the caller.
 */
import axios, { type AxiosRequestConfig } from 'axios'

export const instance = axios.create({
    baseURL: '/',
    withCredentials: true,
})

/**
 * Orval mutator function.
 * Returns the response *data* (not the full Axios response object) so the
 * generated hooks receive the typed payload directly.
 */
export const axiosInstance = <T>(config: AxiosRequestConfig): Promise<T> => {
    return instance(config).then(({ data }) => data as T)
}

export default axiosInstance
