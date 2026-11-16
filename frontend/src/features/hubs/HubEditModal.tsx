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
  type HubDetail,
  type HubMembershipPolicy,
  type HubType,
  type HubUpdateRequest,
} from '../../services/hubsApi'
import './hub-edit-modal.css'

const HUB_CATEGORIES: { value: HubType; label: string }[] = [
  { value: 'company', label: 'Company' },
  { value: 'organisation', label: 'Organisation' },
  { value: 'college', label: 'College' },
  { value: 'college_club', label: 'College Club' },
  { value: 'college_department', label: 'College Department' },
  { value: 'community', label: 'Community' },
]

type EditableField = keyof HubUpdateRequest
type FieldErrors = Partial<Record<EditableField, string>>

interface HubEditFormValues {
  name: string
  hub_type: HubType | ''
  short_description: string
  description: string
  logo: string
  cover_image: string
  website: string
  city: string
  college_or_parent_organisation: string
  membership_policy: HubMembershipPolicy
}

interface HubEditModalProps {
  hub: HubDetail
  canEdit: boolean
  onClose: () => void
  onUpdated: (hub: HubDetail) => void
  onPermissionError: () => void
}

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

function isEditableField(value: string): value is EditableField {
  return [
    'name',
    'hub_type',
    'short_description',
    'description',
    'logo',
    'cover_image',
    'website',
    'city',
    'college_or_parent_organisation',
    'membership_policy',
  ].includes(value)
}

function isHubType(value: string): value is HubType {
  return HUB_CATEGORIES.some((category) => category.value === value)
}

function getRequestError(error: unknown): {
  fieldErrors: FieldErrors
  generalError: string
  permissionChanged: boolean
} {
  if (!axios.isAxiosError(error)) {
    return {
      fieldErrors: {},
      generalError: 'Something went wrong while updating this Hub. Please try again.',
      permissionChanged: false,
    }
  }

  if (!error.response) {
    return {
      fieldErrors: {},
      generalError: 'Unable to reach BYB. Check your connection and try again.',
      permissionChanged: false,
    }
  }

  if (error.response.status === 403) {
    return {
      fieldErrors: {},
      generalError: 'You no longer have permission to edit this Hub.',
      permissionChanged: true,
    }
  }

  if (error.response.status === 404) {
    return {
      fieldErrors: {},
      generalError: 'This Hub is no longer available.',
      permissionChanged: false,
    }
  }

  if (error.response.status >= 500) {
    return {
      fieldErrors: {},
      generalError: 'BYB could not update this Hub right now. Please try again.',
      permissionChanged: false,
    }
  }

  const fieldErrors: FieldErrors = {}
  let generalError = ''
  const responseData: unknown = error.response.data

  if (isRecord(responseData)) {
    for (const [field, value] of Object.entries(responseData)) {
      const message = getErrorText(value)
      if (!message) continue
      if (isEditableField(field)) {
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
      generalError || 'Unable to update this Hub. Please check your details and try again.',
    permissionChanged: false,
  }
}

function FieldError({ id, message }: { id: string; message?: string }) {
  if (!message) return null
  return (
    <span className="hub-edit-field-error" id={id}>
      {message}
    </span>
  )
}

export default function HubEditModal({
  hub,
  canEdit,
  onClose,
  onUpdated,
  onPermissionError,
}: HubEditModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const nameInputRef = useRef<HTMLInputElement>(null)
  const categorySelectRef = useRef<HTMLSelectElement>(null)
  const [values, setValues] = useState<HubEditFormValues>(() => ({
    name: hub.name,
    hub_type: hub.hub_type,
    short_description: hub.short_description,
    description: hub.description,
    logo: hub.logo,
    cover_image: hub.cover_image,
    website: hub.website,
    city: hub.city,
    college_or_parent_organisation: hub.college_or_parent_organisation,
    membership_policy: hub.membership_policy,
  }))
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

  const updateField = <K extends keyof HubEditFormValues>(
    field: K,
    value: HubEditFormValues[K],
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
    if (!canEdit) {
      setGeneralError('You no longer have permission to edit this Hub.')
      return
    }

    const hubType = values.hub_type
    if (!values.name.trim() || !isHubType(hubType)) {
      const nextErrors: FieldErrors = {}
      if (!values.name.trim()) nextErrors.name = 'Enter a Hub name.'
      if (!isHubType(hubType)) nextErrors.hub_type = 'Choose a Hub category.'
      setFieldErrors(nextErrors)
      setGeneralError('Please complete the required fields.')
      if (nextErrors.name) nameInputRef.current?.focus()
      else categorySelectRef.current?.focus()
      return
    }

    if (!event.currentTarget.reportValidity()) return

    const payload: HubUpdateRequest = {
      name: values.name.trim(),
      hub_type: hubType,
      short_description: values.short_description.trim(),
      description: values.description.trim(),
      logo: values.logo.trim(),
      cover_image: values.cover_image.trim(),
      website: values.website.trim(),
      city: values.city.trim(),
      college_or_parent_organisation:
        values.college_or_parent_organisation.trim(),
    }
    if (hub.can_edit_membership_policy) {
      payload.membership_policy = values.membership_policy
    }

    setFieldErrors({})
    setGeneralError('')
    setIsSubmitting(true)

    try {
      const updatedHub = await hubsApi.updateHub(hub.id, payload)
      onUpdated(updatedHub)
    } catch (requestError) {
      const result = getRequestError(requestError)
      setFieldErrors(result.fieldErrors)
      setGeneralError(result.generalError)
      setIsSubmitting(false)
      if (result.permissionChanged) onPermissionError()
    }
  }

  const handleCancel = (event: SyntheticEvent<HTMLDialogElement>) => {
    if (isSubmitting) {
      event.preventDefault()
      return
    }
    onClose()
  }

  const isDisabled = isSubmitting || !canEdit

  return (
    <dialog
      ref={dialogRef}
      className="hub-edit-dialog"
      aria-labelledby="hub-edit-title"
      aria-describedby="hub-edit-description"
      onCancel={handleCancel}
      onClick={(event) => {
        if (event.target === event.currentTarget && !isSubmitting) onClose()
      }}
    >
      <div className="hub-edit-modal">
        <header className="hub-edit-header">
          <div>
            <span className="hub-edit-eyebrow">HUB MANAGEMENT</span>
            <h2 id="hub-edit-title">Edit Hub</h2>
            <p id="hub-edit-description">
              Update the public details for {hub.name}.
            </p>
          </div>
          <button
            className="hub-edit-close"
            type="button"
            aria-label="Close edit Hub form"
            onClick={onClose}
            disabled={isSubmitting}
          >
            ×
          </button>
        </header>

        <form className="hub-edit-form" onSubmit={handleSubmit}>
          <div className="hub-edit-content">
            {generalError && (
              <p className="hub-edit-general-error" role="alert">
                {generalError}
              </p>
            )}

            <div className="hub-edit-grid">
              <div className="hub-edit-field">
                <label htmlFor="hub-edit-name">
                  Hub name <span aria-hidden="true">*</span>
                </label>
                <input
                  ref={nameInputRef}
                  id="hub-edit-name"
                  name="name"
                  type="text"
                  maxLength={200}
                  value={values.name}
                  onChange={(event) => updateField('name', event.currentTarget.value)}
                  aria-invalid={Boolean(fieldErrors.name)}
                  aria-describedby={fieldErrors.name ? 'hub-edit-name-error' : undefined}
                  autoComplete="organization"
                  required
                  disabled={isDisabled}
                />
                <FieldError id="hub-edit-name-error" message={fieldErrors.name} />
              </div>

              <div className="hub-edit-field">
                <label htmlFor="hub-edit-category">
                  Hub category <span aria-hidden="true">*</span>
                </label>
                <select
                  ref={categorySelectRef}
                  id="hub-edit-category"
                  name="hub_type"
                  value={values.hub_type}
                  onChange={(event) => {
                    const value = event.currentTarget.value
                    if (isHubType(value)) updateField('hub_type', value)
                  }}
                  aria-invalid={Boolean(fieldErrors.hub_type)}
                  aria-describedby={
                    fieldErrors.hub_type ? 'hub-edit-category-error' : undefined
                  }
                  required
                  disabled={isDisabled}
                >
                  {HUB_CATEGORIES.map((category) => (
                    <option key={category.value} value={category.value}>
                      {category.label}
                    </option>
                  ))}
                </select>
                <FieldError
                  id="hub-edit-category-error"
                  message={fieldErrors.hub_type}
                />
              </div>

              <div className="hub-edit-field hub-edit-full">
                <label htmlFor="hub-edit-short-description">Short description</label>
                <input
                  id="hub-edit-short-description"
                  name="short_description"
                  type="text"
                  maxLength={300}
                  value={values.short_description}
                  onChange={(event) =>
                    updateField('short_description', event.currentTarget.value)
                  }
                  aria-invalid={Boolean(fieldErrors.short_description)}
                  aria-describedby={
                    fieldErrors.short_description
                      ? 'hub-edit-short-description-error'
                      : undefined
                  }
                  disabled={isDisabled}
                />
                <FieldError
                  id="hub-edit-short-description-error"
                  message={fieldErrors.short_description}
                />
              </div>

              <div className="hub-edit-field hub-edit-full">
                <label htmlFor="hub-edit-description-field">Full description</label>
                <textarea
                  id="hub-edit-description-field"
                  name="description"
                  rows={4}
                  value={values.description}
                  onChange={(event) => updateField('description', event.currentTarget.value)}
                  aria-invalid={Boolean(fieldErrors.description)}
                  aria-describedby={
                    fieldErrors.description ? 'hub-edit-description-error' : undefined
                  }
                  disabled={isDisabled}
                />
                <FieldError
                  id="hub-edit-description-error"
                  message={fieldErrors.description}
                />
              </div>

              <div className="hub-edit-field">
                <label htmlFor="hub-edit-city">City</label>
                <input
                  id="hub-edit-city"
                  name="city"
                  type="text"
                  maxLength={100}
                  value={values.city}
                  onChange={(event) => updateField('city', event.currentTarget.value)}
                  aria-invalid={Boolean(fieldErrors.city)}
                  aria-describedby={fieldErrors.city ? 'hub-edit-city-error' : undefined}
                  disabled={isDisabled}
                />
                <FieldError id="hub-edit-city-error" message={fieldErrors.city} />
              </div>

              <div className="hub-edit-field">
                <label htmlFor="hub-edit-parent">Parent organisation / college</label>
                <input
                  id="hub-edit-parent"
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
                  aria-invalid={Boolean(fieldErrors.college_or_parent_organisation)}
                  aria-describedby={
                    fieldErrors.college_or_parent_organisation
                      ? 'hub-edit-parent-error'
                      : undefined
                  }
                  disabled={isDisabled}
                />
                <FieldError
                  id="hub-edit-parent-error"
                  message={fieldErrors.college_or_parent_organisation}
                />
              </div>

              <div className="hub-edit-field">
                <label htmlFor="hub-edit-website">Website</label>
                <input
                  id="hub-edit-website"
                  name="website"
                  type="url"
                  maxLength={500}
                  value={values.website}
                  onChange={(event) => updateField('website', event.currentTarget.value)}
                  aria-invalid={Boolean(fieldErrors.website)}
                  aria-describedby={
                    fieldErrors.website ? 'hub-edit-website-error' : undefined
                  }
                  disabled={isDisabled}
                />
                <FieldError id="hub-edit-website-error" message={fieldErrors.website} />
              </div>

              <div className="hub-edit-field">
                <label htmlFor="hub-edit-logo">Logo URL</label>
                <input
                  id="hub-edit-logo"
                  name="logo"
                  type="url"
                  maxLength={500}
                  value={values.logo}
                  onChange={(event) => updateField('logo', event.currentTarget.value)}
                  aria-invalid={Boolean(fieldErrors.logo)}
                  aria-describedby={fieldErrors.logo ? 'hub-edit-logo-error' : undefined}
                  disabled={isDisabled}
                />
                <FieldError id="hub-edit-logo-error" message={fieldErrors.logo} />
              </div>

              <div className="hub-edit-field">
                <label htmlFor="hub-edit-cover">Cover image URL</label>
                <input
                  id="hub-edit-cover"
                  name="cover_image"
                  type="url"
                  maxLength={500}
                  value={values.cover_image}
                  onChange={(event) => updateField('cover_image', event.currentTarget.value)}
                  aria-invalid={Boolean(fieldErrors.cover_image)}
                  aria-describedby={
                    fieldErrors.cover_image ? 'hub-edit-cover-error' : undefined
                  }
                  disabled={isDisabled}
                />
                <FieldError
                  id="hub-edit-cover-error"
                  message={fieldErrors.cover_image}
                />
              </div>

              {hub.can_edit_membership_policy && (
                <fieldset
                  className="hub-edit-policy hub-edit-full"
                  aria-describedby={
                    fieldErrors.membership_policy
                      ? 'hub-edit-policy-error'
                      : undefined
                  }
                  disabled={isDisabled}
                >
                  <legend>Membership policy</legend>
                  <label className="hub-edit-policy-option">
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
                  <label className="hub-edit-policy-option">
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
                    id="hub-edit-policy-error"
                    message={fieldErrors.membership_policy}
                  />
                </fieldset>
              )}
            </div>
          </div>

          <footer className="hub-edit-footer">
            <button
              className="hub-edit-cancel"
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              className="hub-edit-submit"
              type="submit"
              disabled={isDisabled}
            >
              {isSubmitting ? (
                <>
                  <span className="hub-edit-spinner" aria-hidden="true" />
                  Saving...
                </>
              ) : (
                'Save changes'
              )}
            </button>
          </footer>
        </form>
      </div>
    </dialog>
  )
}
