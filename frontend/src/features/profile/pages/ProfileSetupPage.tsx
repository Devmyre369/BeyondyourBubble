
import { useEffect, useState, type ChangeEvent, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

import AuthLayout from '../../auth/components/AuthLayout'
import { useAuth } from '../../../context/AuthContext'
import profileApi, {
  type CreateProfileData,
  type ProfileType,
  type UserProfile,
} from '../../../services/profileApi'

import './profile.css'

interface FormState {
  first_name: string
  last_name: string
  profile_type: ProfileType
  byb_signature: string
  bio: string
  city: string

  institution: string
  course: string
  field_of_study: string
  academic_year: string
  graduation_year: string

  current_organization: string
  job_title: string
  industry: string
  experience_years: string

  interests: string
  skills: string

  linkedin_url: string
  github_url: string
  website_url: string

  visibility: 'public' | 'private'
}

const initialForm: FormState = {
  first_name: '',
  last_name: '',
  profile_type: 'student',

  byb_signature: '',
  bio: '',
  city: '',

  institution: '',
  course: '',
  field_of_study: '',
  academic_year: '',
  graduation_year: '',

  current_organization: '',
  job_title: '',
  industry: '',
  experience_years: '',

  interests: '',
  skills: '',

  linkedin_url: '',
  github_url: '',
  website_url: '',

  visibility: 'public',
}

const MAX_PROFILE_SIZE = 5 * 1024 * 1024
const MAX_COVER_SIZE = 10 * 1024 * 1024

const ALLOWED_IMAGE_TYPES = [
  'image/jpeg',
  'image/png',
  'image/webp',
]

function splitList(value: string): string[] {
  return [
    ...new Set(
      value
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean)
    ),
  ]
}

function TextField({
  label,
  name,
  value,
  onChange,
  placeholder,
  required = false,
  type = 'text',
}: {
  label: string
  name: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
  required?: boolean
  type?: string
}) {
  return (
    <div className="form-group">
      <label htmlFor={name}>
        {label}
        {required && <span className="required-mark"> *</span>}
      </label>

      <input
        id={name}
        name={name}
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        required={required}
        maxLength={type === 'url' ? 2048 : 150}
      />
    </div>
  )
}

function validateImage(
  file: File,
  imageType: 'profile_picture' | 'cover_image'
): string | null {
  if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
    return 'Only JPG, JPEG, PNG, and WEBP images are allowed.'
  }

  const maxSize =
    imageType === 'profile_picture'
      ? MAX_PROFILE_SIZE
      : MAX_COVER_SIZE

  const maxSizeLabel = imageType === 'profile_picture' ? '5 MB' : '10 MB'

  if (file.size > maxSize) {
    return `Image size must not exceed ${maxSizeLabel}.`
  }

  return null
}

export default function ProfileSetupPage() {
  const navigate = useNavigate()
  const { setProfile } = useAuth()

  const [form, setForm] = useState<FormState>(initialForm)

  const [profilePicture, setProfilePicture] = useState<File | null>(null)
  const [coverImage, setCoverImage] = useState<File | null>(null)

  const [profilePreview, setProfilePreview] = useState('')
  const [coverPreview, setCoverPreview] = useState('')

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    return () => {
      if (profilePreview) {
        URL.revokeObjectURL(profilePreview)
      }

      if (coverPreview) {
        URL.revokeObjectURL(coverPreview)
      }
    }
  }, [profilePreview, coverPreview])

  const updateField = <K extends keyof FormState>(
    key: K,
    value: FormState[K]
  ) => {
    setForm((previous) => ({
      ...previous,
      [key]: value,
    }))
  }

  const handleImageChange = (
    event: ChangeEvent<HTMLInputElement>,
    imageType: 'profile_picture' | 'cover_image'
  ) => {
    const file = event.target.files?.[0]

    if (!file) return

    const validationError = validateImage(file, imageType)

    if (validationError) {
      setError(validationError)
      event.target.value = ''
      return
    }

    setError('')

    const previewUrl = URL.createObjectURL(file)

    if (imageType === 'profile_picture') {
      setProfilePicture(file)
      setProfilePreview(previewUrl)
    } else {
      setCoverImage(file)
      setCoverPreview(previewUrl)
    }
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')

    if (!form.first_name.trim() || !form.last_name.trim()) {
      setError('First name and last name are required.')
      return
    }

    const payload: CreateProfileData = {
      first_name: form.first_name.trim(),
      last_name: form.last_name.trim(),

      profile_type: form.profile_type,

      byb_signature: form.byb_signature.trim() || null,
      bio: form.bio.trim(),
      city: form.city.trim(),

      institution: form.institution.trim(),
      course: form.course.trim(),
      field_of_study: form.field_of_study.trim(),
      academic_year: form.academic_year.trim(),
      graduation_year: form.graduation_year
        ? Number(form.graduation_year)
        : null,

      current_organization: form.current_organization.trim(),
      job_title: form.job_title.trim(),
      industry: form.industry.trim(),
      experience_years: form.experience_years
        ? Number(form.experience_years)
        : null,

      interests: splitList(form.interests),
      skills: splitList(form.skills),

      linkedin_url: form.linkedin_url.trim(),
      github_url: form.github_url.trim(),
      website_url: form.website_url.trim(),

      visibility: form.visibility,
    }

    setLoading(true)

    try {
      let updatedProfile: UserProfile =
        await profileApi.createProfile(payload)

      if (profilePicture) {
        updatedProfile = await profileApi.uploadProfileImage(
          'profile_picture',
          profilePicture
        )
      }

      if (coverImage) {
        updatedProfile = await profileApi.uploadProfileImage(
          'cover_image',
          coverImage
        )
      }

      setProfile(updatedProfile)

      navigate('/home', { replace: true })
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const data = err.response?.data

        if (data?.profile) {
          setError(
            'A profile already exists for this account. Please log in again.'
          )
        } else if (data && typeof data === 'object') {
          const messages = Object.entries(data)
            .flatMap(([field, value]) => {
              if (Array.isArray(value)) {
                return value.map((message) => `${field}: ${message}`)
              }

              return typeof value === 'string'
                ? [`${field}: ${value}`]
                : []
            })

          setError(
            messages.length
              ? messages.join(' ')
              : 'Unable to create your profile. Please check your details.'
          )
        } else {
          setError('Unable to connect to BYB. Please try again.')
        }
      } else {
        setError('Something went wrong. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthLayout
      eyebrow="YOUR BYB IDENTITY"
      title="Build your VibeSpace."
      subtitle="Tell the BYB community who you are. You can update these details later."
    >
      <form className="auth-form profile-onboarding" onSubmit={handleSubmit}>
        <div className="profile-section-heading">
          <span className="profile-step">01</span>
          <div>
            <h3>Your identity</h3>
            <p>Start with the basics.</p>
          </div>
        </div>

        <div className="profile-form-grid">
          <TextField
            label="First name"
            name="first_name"
            value={form.first_name}
            onChange={(value) => updateField('first_name', value)}
            placeholder="Your first name"
            required
          />

          <TextField
            label="Last name"
            name="last_name"
            value={form.last_name}
            onChange={(value) => updateField('last_name', value)}
            placeholder="Your last name"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="profile_type">I identify as</label>

          <select
            id="profile_type"
            name="profile_type"
            value={form.profile_type}
            onChange={(event) =>
              updateField(
                'profile_type',
                event.target.value as ProfileType
              )
            }
          >
            <option value="student">Student</option>
            <option value="professional">Professional</option>
          </select>
        </div>

        <TextField
          label="BYB signature"
          name="byb_signature"
          value={form.byb_signature}
          onChange={(value) => updateField('byb_signature', value)}
          placeholder="Choose your unique BYB identity"
        />

        <div className="profile-section-heading">
          <span className="profile-step">02</span>
          <div>
            <h3>
              {form.profile_type === 'student'
                ? 'Your academic world'
                : 'Your professional world'}
            </h3>
            <p>
              {form.profile_type === 'student'
                ? 'Tell us where you study and what you explore.'
                : 'Tell us about your work and experience.'}
            </p>
          </div>
        </div>

        {form.profile_type === 'student' ? (
          <>
            <TextField
              label="Institution / College"
              name="institution"
              value={form.institution}
              onChange={(value) => updateField('institution', value)}
              placeholder="Your college or university"
            />

            <div className="profile-form-grid">
              <TextField
                label="Course"
                name="course"
                value={form.course}
                onChange={(value) => updateField('course', value)}
                placeholder="e.g. B.Tech"
              />

              <TextField
                label="Field of study"
                name="field_of_study"
                value={form.field_of_study}
                onChange={(value) => updateField('field_of_study', value)}
                placeholder="e.g. Computer Science"
              />
            </div>

            <div className="profile-form-grid">
              <TextField
                label="Academic year"
                name="academic_year"
                value={form.academic_year}
                onChange={(value) => updateField('academic_year', value)}
                placeholder="e.g. 2nd Year"
              />

              <TextField
                label="Graduation year"
                name="graduation_year"
                type="number"
                value={form.graduation_year}
                onChange={(value) => updateField('graduation_year', value)}
                placeholder="e.g. 2028"
              />
            </div>
          </>
        ) : (
          <>
            <TextField
              label="Current organisation"
              name="current_organization"
              value={form.current_organization}
              onChange={(value) => updateField('current_organization', value)}
              placeholder="Where do you work?"
            />

            <div className="profile-form-grid">
              <TextField
                label="Job title"
                name="job_title"
                value={form.job_title}
                onChange={(value) => updateField('job_title', value)}
                placeholder="e.g. Software Engineer"
              />

              <TextField
                label="Industry"
                name="industry"
                value={form.industry}
                onChange={(value) => updateField('industry', value)}
                placeholder="e.g. Technology"
              />
            </div>

            <TextField
              label="Years of experience"
              name="experience_years"
              type="number"
              value={form.experience_years}
              onChange={(value) => updateField('experience_years', value)}
              placeholder="e.g. 3"
            />
          </>
        )}

        <div className="profile-section-heading">
          <span className="profile-step">03</span>
          <div>
            <h3>About you</h3>
            <p>Give people a glimpse into your world.</p>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="bio">Your bio</label>

          <textarea
            id="bio"
            name="bio"
            rows={4}
            maxLength={500}
            value={form.bio}
            onChange={(event) => updateField('bio', event.target.value)}
            placeholder="What interests you? What are you passionate about?"
          />

          <span className="profile-field-hint">
            {form.bio.length}/500 characters
          </span>
        </div>

        <TextField
          label="City"
          name="city"
          value={form.city}
          onChange={(value) => updateField('city', value)}
          placeholder="Your current city"
        />

        <div className="form-group">
          <label htmlFor="interests">Interests</label>

          <input
            id="interests"
            name="interests"
            value={form.interests}
            onChange={(event) => updateField('interests', event.target.value)}
            placeholder="Technology, music, sports, travel"
          />

          <span className="profile-field-hint">
            Separate interests with commas.
          </span>
        </div>

        <div className="form-group">
          <label htmlFor="skills">Skills</label>

          <input
            id="skills"
            name="skills"
            value={form.skills}
            onChange={(event) => updateField('skills', event.target.value)}
            placeholder="Python, design, leadership"
          />

          <span className="profile-field-hint">
            Separate skills with commas.
          </span>
        </div>

        <div className="profile-section-heading">
          <span className="profile-step">04</span>
          <div>
            <h3>Your online presence</h3>
            <p>Personalise your VibeSpace with images and links.</p>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="profile_picture">Profile picture</label>

          <input
            id="profile_picture"
            name="profile_picture"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={(event) =>
              handleImageChange(event, 'profile_picture')
            }
          />

          <span className="profile-field-hint">
            JPG, PNG or WEBP. Maximum size: 5 MB.
          </span>

          {profilePreview && (
            <div className="profile-image-preview">
              <img src={profilePreview} alt="Profile picture preview" />
            </div>
          )}
        </div>

        <div className="form-group">
          <label htmlFor="cover_image">Cover image</label>

          <input
            id="cover_image"
            name="cover_image"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={(event) =>
              handleImageChange(event, 'cover_image')
            }
          />

          <span className="profile-field-hint">
            JPG, PNG or WEBP. Maximum size: 10 MB.
          </span>

          {coverPreview && (
            <div className="cover-image-preview">
              <img src={coverPreview} alt="Cover image preview" />
            </div>
          )}
        </div>

        <TextField
          label="LinkedIn URL"
          name="linkedin_url"
          type="url"
          value={form.linkedin_url}
          onChange={(value) => updateField('linkedin_url', value)}
          placeholder="https://linkedin.com/in/username"
        />

        <TextField
          label="GitHub URL"
          name="github_url"
          type="url"
          value={form.github_url}
          onChange={(value) => updateField('github_url', value)}
          placeholder="https://github.com/username"
        />

        <TextField
          label="Personal website"
          name="website_url"
          type="url"
          value={form.website_url}
          onChange={(value) => updateField('website_url', value)}
          placeholder="https://yourwebsite.com"
        />

        <div className="profile-section-heading">
          <span className="profile-step">05</span>
          <div>
            <h3>Privacy</h3>
            <p>Choose who can discover your VibeSpace.</p>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="visibility">Profile visibility</label>

          <select
            id="visibility"
            name="visibility"
            value={form.visibility}
            onChange={(event) =>
              updateField(
                'visibility',
                event.target.value as 'public' | 'private'
              )
            }
          >
            <option value="public">
              Public — visible to the BYB community
            </option>
            <option value="private">
              Private — restrict public profile visibility
            </option>
          </select>
        </div>

        {error && (
          <div className="auth-error" role="alert">
            {error}
          </div>
        )}

        <button
          type="submit"
          className="auth-submit-button"
          disabled={loading}
        >
          {loading ? 'Creating your VibeSpace...' : 'Create my VibeSpace'}
        </button>

        <p className="profile-submit-note">
          Your profile details can be edited later.
        </p>
      </form>
    </AuthLayout>
  )
}
