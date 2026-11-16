import axios from 'axios'
import {
  type FormEvent,
  type SyntheticEvent,
  useEffect,
  useRef,
  useState,
} from 'react'

import {
  hubsApi,
  type HubCreateRequest,
  type HubDetail,
  type HubMembershipPolicy,
  type HubType,
} from '../../services/hubsApi'
import './hub-create-modal.css'

const HUB_CATEGORIES: { value: HubType; label: string }[] = [
  { value: 'company', label: 'Company' },
  { value: 'organisation', label: 'Organisation' },
  { value: 'college', label: 'College' },
  { value: 'college_club', label: 'College Club' },
  { value: 'college_department', label: 'College Department' },
  { value: 'community', label: 'Community' },
]

type HubCreateField = keyof HubCreateRequest
type FieldErrors = Partial<Record<HubCreateField, string>>

interface HubCreateFormValues {
  name: string
  hub_type: HubType | ''
  membership_policy: HubMembershipPolicy
  short_description: string
  description: string
  city: string
  college_or_parent_organisation: string
  website: string
  contact_email: string
  logo: string
  cover_image: string
}

interface HubCreateModalProps {
  onClose: () => void
  onCreated: (hub: HubDetail) => void
}

const INITIAL_VALUES: HubCreateFormValues = {
  name: '',
  hub_type: '',
  membership_policy: 'approval_required',
  short_description: '',
  description: '',
  city: '',
  college_or_parent_organisation: '',
  website: '',
  contact_email: '',
  logo: '',
  cover_image: '',
}

const FORM_FIELDS: HubCreateField[] = [
  'name',
  'hub_type',
  'membership_policy',
  'short_description',
  'description',
  'city',
  'college_or_parent_organisation',
  'website',
  'contact_email',
  'logo',
  'cover_image',
]

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function getErrorText(value: unknown): string {
  if (typeof value === 'string') return value
  if (Array.isArray(value)) {
    return value.map(getErrorText).filter(Boolean).join(' ')
  }
  return ''
}

function isHubCreateField(value: string): value is HubCreateField {
  return FORM_FIELDS.some((field) => field === value)
}

function isHubType(value: string): value is HubType {
  return HUB_CATEGORIES.some((category) => category.value === value)
}

function getRequestError(error: unknown): {
  fieldErrors: FieldErrors
  generalError: string
} {
  if (!axios.isAxiosError(error)) {
    return {
      fieldErrors: {},
      generalError: 'Something went wrong while creating this Hub. Please try again.',
    }
  }

  if (!error.response) {
    return {
      fieldErrors: {},
      generalError: 'Unable to reach BYB. Check your connection and try again.',
    }
  }

  if (error.response.status >= 500) {
    return {
      fieldErrors: {},
      generalError: 'BYB could not create this Hub right now. Please try again.',
    }
  }

  const fieldErrors: FieldErrors = {}
  let generalError = ''
  const responseData: unknown = error.response.data

  if (isRecord(responseData)) {
    for (const [field, value] of Object.entries(responseData)) {
      const message = getErrorText(value)
      if (!message) continue

      if (isHubCreateField(field)) {
        fieldErrors[field] = message
      } else {
        generalError = message
      }
    }
  } else {
    generalError = getErrorText(responseData)
  }

  if (!generalError && Object.keys(fieldErrors).length > 0) {
    generalError = 'Please review the highlighted fields.'
  }

  return {
    fieldErrors,
    generalError:
      generalError || 'Unable to create this Hub. Please check your details and try again.',
  }
}

function FieldError({ id, message }: { id: string; message?: string }) {
  if (!message) return null

  return (
    <span className="hub-create-field-error" id={id}>
      {message}
    </span>
  )
}

export default function HubCreateModal({
  onClose,
  onCreated,
}: HubCreateModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const nameInputRef = useRef<HTMLInputElement>(null)
  const categorySelectRef = useRef<HTMLSelectElement>(null)
  const [values, setValues] = useState(INITIAL_VALUES)
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})
  const [generalError, setGeneralError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return

    const previousBodyOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'

    if (!dialog.open) dialog.showModal()
    nameInputRef.current?.focus()

    return () => {
      if (dialog.open) dialog.close()
      document.body.style.overflow = previousBodyOverflow
    }
  }, [])

  const updateField = <K extends keyof HubCreateFormValues>(
    field: K,
    value: HubCreateFormValues[K],
  ) => {
    setValues((previous) => ({ ...previous, [field]: value }))
    setFieldErrors((previous) => {
      if (!previous[field]) return previous
      const next = { ...previous }
      delete next[field]
      return next
    })
    setGeneralError('')
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (isSubmitting) return

    const hubType = values.hub_type
    if (!values.name.trim() || !isHubType(hubType)) {
      const nextErrors: FieldErrors = {}
      if (!values.name.trim()) nextErrors.name = 'Enter a Hub name.'
      if (!isHubType(hubType)) {
        nextErrors.hub_type = 'Choose a Hub category.'
      }

      setFieldErrors(nextErrors)
      setGeneralError('Please complete the required fields.')
      if (nextErrors.name) {
        nameInputRef.current?.focus()
      } else {
        categorySelectRef.current?.focus()
      }
      return
    }

    if (!event.currentTarget.reportValidity()) return

    const payload: HubCreateRequest = {
      name: values.name.trim(),
      hub_type: hubType,
      membership_policy: values.membership_policy,
      short_description: values.short_description.trim(),
      description: values.description.trim(),
      city: values.city.trim(),
      college_or_parent_organisation:
        values.college_or_parent_organisation.trim(),
      website: values.website.trim(),
      contact_email: values.contact_email.trim(),
      logo: values.logo.trim(),
      cover_image: values.cover_image.trim(),
    }

    setFieldErrors({})
    setGeneralError('')
    setIsSubmitting(true)

    try {
      const hub = await hubsApi.createHub(payload)
      onCreated(hub)
    } catch (requestError) {
      const result = getRequestError(requestError)
      setFieldErrors(result.fieldErrors)
      setGeneralError(result.generalError)
      setIsSubmitting(false)
    }
  }

  const handleCancel = (event: SyntheticEvent<HTMLDialogElement>) => {
    if (isSubmitting) {
      event.preventDefault()
      return
    }

    onClose()
  }

  return (
    <dialog
      ref={dialogRef}
      className="hub-create-dialog"
      aria-labelledby="hub-create-title"
      aria-describedby="hub-create-description"
      onCancel={handleCancel}
      onClick={(event) => {
        if (
          event.target === event.currentTarget &&
          !isSubmitting
        ) {
          onClose()
        }
      }}
    >
      <div className="hub-create-modal">
        <header className="hub-create-modal-header">
          <div>
            <span className="hub-create-eyebrow">BUILD YOUR SPACE</span>
            <h2 id="hub-create-title">Create a Hub</h2>
            <p id="hub-create-description">
              Give your community a public home on BYB.
            </p>
          </div>
          <button
            className="hub-create-close"
            type="button"
            aria-label="Close create Hub form"
            onClick={onClose}
            disabled={isSubmitting}
          >
            ×
          </button>
        </header>

        <form className="hub-create-form" onSubmit={handleSubmit}>
          <div className="hub-create-form-content">
            {generalError && (
              <p className="hub-create-general-error" role="alert">
                {generalError}
              </p>
            )}

            <div className="hub-create-form-grid">
              <div className="hub-create-field">
                <label htmlFor="hub-create-name">
                  Hub name <span aria-hidden="true">*</span>
                </label>
                <input
                  ref={nameInputRef}
                  id="hub-create-name"
                  name="name"
                  type="text"
                  maxLength={200}
                  value={values.name}
                  onChange={(event) =>
                    updateField('name', event.currentTarget.value)
                  }
                  aria-invalid={Boolean(fieldErrors.name)}
                  aria-describedby={
                    fieldErrors.name ? 'hub-create-name-error' : undefined
                  }
                  autoComplete="organization"
                  required
                />
                <FieldError
                  id="hub-create-name-error"
                  message={fieldErrors.name}
                />
              </div>

              <div className="hub-create-field">
                <label htmlFor="hub-create-category">
                  Hub category <span aria-hidden="true">*</span>
                </label>
                <select
                  ref={categorySelectRef}
                  id="hub-create-category"
                  name="hub_type"
                  value={values.hub_type}
                  onChange={(event) => {
                    const value = event.currentTarget.value
                    if (value === '' || isHubType(value)) {
                      updateField('hub_type', value)
                    }
                  }}
                  aria-invalid={Boolean(fieldErrors.hub_type)}
                  aria-describedby={
                    fieldErrors.hub_type
                      ? 'hub-create-category-error'
                      : undefined
                  }
                  required
                >
                  <option value="">Select a category</option>
                  {HUB_CATEGORIES.map((category) => (
                    <option key={category.value} value={category.value}>
                      {category.label}
                    </option>
                  ))}
                </select>
                <FieldError
                  id="hub-create-category-error"
                  message={fieldErrors.hub_type}
                />
              </div>

              <div className="hub-create-field hub-create-field-full">
                <label htmlFor="hub-create-short-description">
                  Short description
                </label>
                <input
                  id="hub-create-short-description"
                  name="short_description"
                  type="text"
                  maxLength={300}
                  value={values.short_description}
                  onChange={(event) =>
                    updateField(
                      'short_description',
                      event.currentTarget.value,
                    )
                  }
                  aria-invalid={Boolean(fieldErrors.short_description)}
                  aria-describedby={
                    fieldErrors.short_description
                      ? 'hub-create-short-description-error'
                      : undefined
                  }
                />
                <FieldError
                  id="hub-create-short-description-error"
                  message={fieldErrors.short_description}
                />
              </div>

              <div className="hub-create-field hub-create-field-full">
                <label htmlFor="hub-create-full-description">
                  Full description
                </label>
                <textarea
                  id="hub-create-full-description"
                  name="description"
                  rows={4}
                  value={values.description}
                  onChange={(event) =>
                    updateField('description', event.currentTarget.value)
                  }
                  aria-invalid={Boolean(fieldErrors.description)}
                  aria-describedby={
                    fieldErrors.description
                      ? 'hub-create-full-description-error'
                      : undefined
                  }
                />
                <FieldError
                  id="hub-create-full-description-error"
                  message={fieldErrors.description}
                />
              </div>

              <div className="hub-create-field">
                <label htmlFor="hub-create-city">City</label>
                <input
                  id="hub-create-city"
                  name="city"
                  type="text"
                  maxLength={100}
                  value={values.city}
                  onChange={(event) =>
                    updateField('city', event.currentTarget.value)
                  }
                  aria-invalid={Boolean(fieldErrors.city)}
                  aria-describedby={
                    fieldErrors.city ? 'hub-create-city-error' : undefined
                  }
                />
                <FieldError
                  id="hub-create-city-error"
                  message={fieldErrors.city}
                />
              </div>

              <div className="hub-create-field">
                <label htmlFor="hub-create-parent">
                  Parent organisation / college
                </label>
                <input
                  id="hub-create-parent"
                  name="college_or_parent_organisation"
                  type="text"
                  maxLength={200}
                  value={values.college_or_parent_organisation}
                  onChange={(event) =>
                    updateField(
                      'college_or_parent_organisation',
                      event.currentTarget.value,
                    )
                  }
                  aria-invalid={Boolean(
                    fieldErrors.college_or_parent_organisation,
                  )}
                  aria-describedby={
                    fieldErrors.college_or_parent_organisation
                      ? 'hub-create-parent-error'
                      : undefined
                  }
                />
                <FieldError
                  id="hub-create-parent-error"
                  message={fieldErrors.college_or_parent_organisation}
                />
              </div>

              <div className="hub-create-field">
                <label htmlFor="hub-create-website">Website</label>
                <input
                  id="hub-create-website"
                  name="website"
                  type="url"
                  maxLength={500}
                  value={values.website}
                  onChange={(event) =>
                    updateField('website', event.currentTarget.value)
                  }
                  aria-invalid={Boolean(fieldErrors.website)}
                  aria-describedby={
                    fieldErrors.website
                      ? 'hub-create-website-error'
                      : undefined
                  }
                />
                <FieldError
                  id="hub-create-website-error"
                  message={fieldErrors.website}
                />
              </div>

              <div className="hub-create-field">
                <label htmlFor="hub-create-email">Contact email</label>
                <input
                  id="hub-create-email"
                  name="contact_email"
                  type="email"
                  maxLength={254}
                  value={values.contact_email}
                  onChange={(event) =>
                    updateField('contact_email', event.currentTarget.value)
                  }
                  aria-invalid={Boolean(fieldErrors.contact_email)}
                  aria-describedby={
                    fieldErrors.contact_email
                      ? 'hub-create-email-error'
                      : undefined
                  }
                  autoComplete="email"
                />
                <FieldError
                  id="hub-create-email-error"
                  message={fieldErrors.contact_email}
                />
              </div>

              <div className="hub-create-field">
                <label htmlFor="hub-create-logo">Logo URL</label>
                <input
                  id="hub-create-logo"
                  name="logo"
                  type="url"
                  maxLength={500}
                  value={values.logo}
                  onChange={(event) =>
                    updateField('logo', event.currentTarget.value)
                  }
                  aria-invalid={Boolean(fieldErrors.logo)}
                  aria-describedby={
                    fieldErrors.logo ? 'hub-create-logo-error' : undefined
                  }
                />
                <FieldError
                  id="hub-create-logo-error"
                  message={fieldErrors.logo}
                />
              </div>

              <div className="hub-create-field">
                <label htmlFor="hub-create-cover">Cover image URL</label>
                <input
                  id="hub-create-cover"
                  name="cover_image"
                  type="url"
                  maxLength={500}
                  value={values.cover_image}
                  onChange={(event) =>
                    updateField('cover_image', event.currentTarget.value)
                  }
                  aria-invalid={Boolean(fieldErrors.cover_image)}
                  aria-describedby={
                    fieldErrors.cover_image
                      ? 'hub-create-cover-error'
                      : undefined
                  }
                />
                <FieldError
                  id="hub-create-cover-error"
                  message={fieldErrors.cover_image}
                />
              </div>

              <fieldset
                className="hub-create-policy hub-create-field-full"
                aria-describedby={
                  fieldErrors.membership_policy
                    ? 'hub-create-policy-error'
                    : undefined
                }
              >
                <legend>Membership policy</legend>
                <label className="hub-create-policy-option">
                  <input
                    type="radio"
                    name="membership_policy"
                    value="approval_required"
                    checked={values.membership_policy === 'approval_required'}
                    onChange={() =>
                      updateField('membership_policy', 'approval_required')
                    }
                  />
                  <span>
                    <strong>Approval required</strong>
                    <small>Review requests before people can join.</small>
                  </span>
                </label>
                <label className="hub-create-policy-option">
                  <input
                    type="radio"
                    name="membership_policy"
                    value="open"
                    checked={values.membership_policy === 'open'}
                    onChange={() => updateField('membership_policy', 'open')}
                  />
                  <span>
                    <strong>Open membership</strong>
                    <small>Anyone can join this Hub.</small>
                  </span>
                </label>
                <FieldError
                  id="hub-create-policy-error"
                  message={fieldErrors.membership_policy}
                />
              </fieldset>
            </div>
          </div>

          <footer className="hub-create-modal-footer">
            <button
              className="hub-create-cancel"
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              className="hub-create-submit"
              type="submit"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <span className="hub-create-submit-spinner" aria-hidden="true" />
                  Creating...
                </>
              ) : (
                'Create Hub'
              )}
            </button>
          </footer>
        </form>
      </div>
    </dialog>
  )
}
