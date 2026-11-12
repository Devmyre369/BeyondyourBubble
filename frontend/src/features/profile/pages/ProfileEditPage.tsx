
import { useEffect, useState, type ChangeEvent, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { useAuth } from '../../../context/AuthContext'
import profileApi, {
  type CreateProfileData,
  type ProfileImageType,
} from '../../../services/profileApi'

import './profile.css'
import './vibespace.css'

const initialForm: CreateProfileData = {
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
  graduation_year: null,
  current_organization: '',
  job_title: '',
  industry: '',
  experience_years: null,
  interests: [],
  skills: [],
  linkedin_url: '',
  github_url: '',
  website_url: '',
  visibility: 'public',
}

const allowedTypes = ['image/jpeg', 'image/png', 'image/webp']

export default function ProfileEditPage() {
  const navigate = useNavigate()
  const { profile, setProfile } = useAuth()

  const [form, setForm] = useState<CreateProfileData>(initialForm)
  const [interestsText, setInterestsText] = useState('')
  const [skillsText, setSkillsText] = useState('')

  const [profilePicture, setProfilePicture] = useState<File | null>(null)
  const [coverImage, setCoverImage] = useState<File | null>(null)

  const [profilePreview, setProfilePreview] = useState('')
  const [coverPreview, setCoverPreview] = useState('')

  const [removeProfilePicture, setRemoveProfilePicture] = useState(false)
  const [removeCoverImage, setRemoveCoverImage] = useState(false)

  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    if (!profile) return

    setForm({
      first_name: profile.first_name || '',
      last_name: profile.last_name || '',
      profile_type: profile.profile_type,
      byb_signature: profile.byb_signature || '',
      bio: profile.bio || '',
      city: profile.city || '',
      institution: profile.institution || '',
      course: profile.course || '',
      field_of_study: profile.field_of_study || '',
      academic_year: profile.academic_year || '',
      graduation_year: profile.graduation_year,
      current_organization: profile.current_organization || '',
      job_title: profile.job_title || '',
      industry: profile.industry || '',
      experience_years: profile.experience_years,
      interests: profile.interests || [],
      skills: profile.skills || [],
      linkedin_url: profile.linkedin_url || '',
      github_url: profile.github_url || '',
      website_url: profile.website_url || '',
      visibility: profile.visibility || 'public',
    })

    setInterestsText((profile.interests || []).join(', '))
    setSkillsText((profile.skills || []).join(', '))
  }, [profile])

  useEffect(() => {
    return () => {
      if (profilePreview) URL.revokeObjectURL(profilePreview)
      if (coverPreview) URL.revokeObjectURL(coverPreview)
    }
  }, [profilePreview, coverPreview])

  if (!profile) {
    return <div className="profile-loading">Loading profile...</div>
  }

  const updateField = (name: keyof CreateProfileData, value: string | number | null) => {
    setForm((previous) => ({
      ...previous,
      [name]: value,
    }))
  }

  const handleImageChange = (
    event: ChangeEvent<HTMLInputElement>,
    imageType: ProfileImageType
  ) => {
    const file = event.target.files?.[0]
    if (!file) return

    const maxSize = imageType === 'profile_picture'
      ? 5 * 1024 * 1024
      : 10 * 1024 * 1024

    if (!allowedTypes.includes(file.type)) {
      setError('Please select a JPG, PNG or WEBP image.')
      event.target.value = ''
      return
    }

    if (file.size > maxSize) {
      setError(
        imageType === 'profile_picture'
          ? 'Profile picture must be 5 MB or smaller.'
          : 'Cover image must be 10 MB or smaller.'
      )
      event.target.value = ''
      return
    }

    setError('')

    if (imageType === 'profile_picture') {
      setProfilePicture(file)
      setProfilePreview(URL.createObjectURL(file))
      setRemoveProfilePicture(false)
    } else {
      setCoverImage(file)
      setCoverPreview(URL.createObjectURL(file))
      setRemoveCoverImage(false)
    }
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    setError('')
    setSuccess('')

    if (!form.first_name.trim() || !form.last_name.trim()) {
      setError('First name and last name are required.')
      return
    }

    const updatedData: CreateProfileData = {
      ...form,
      first_name: form.first_name.trim(),
      last_name: form.last_name.trim(),
      interests: interestsText
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean),
      skills: skillsText
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean),
    }

    setSaving(true)

    try {
      let updatedProfile = await profileApi.updateProfile(updatedData)

      if (removeProfilePicture && !profilePicture && updatedProfile.profile_picture) {
        updatedProfile = await profileApi.deleteProfileImage('profile_picture')
      }

      if (removeCoverImage && !coverImage && updatedProfile.cover_image) {
        updatedProfile = await profileApi.deleteProfileImage('cover_image')
      }

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
      setSuccess('Your profile has been updated successfully.')

      navigate('/home')
    } catch (err: unknown) {
      console.error('Profile update failed:', err)
      setError('Unable to update your profile. Please check your details and try again.')
    } finally {
      setSaving(false)
    }
  }

  const ImagePreview = ({
    title,
    image,
    preview,
    onChange,
    onRemove,
    isRemoved,
  }: {
    title: string
    image: string
    preview: string
    onChange: (event: ChangeEvent<HTMLInputElement>) => void
    onRemove: () => void
    isRemoved: boolean
  }) => (
    <div className="profile-edit-image-field">
      <label>{title}</label>

      {(preview || (image && !isRemoved)) && (
        <div className="profile-edit-image-preview">
          <img
            src={preview || image}
            alt={`${title} preview`}
          />
        </div>
      )}

      {isRemoved && !preview && (
        <p className="vibespace-empty-note">Image will be removed when you save.</p>
      )}

      <input
        type="file"
        accept="image/jpeg,image/png,image/webp"
        onChange={onChange}
      />

      <button
        type="button"
        className="profile-edit-remove-button"
        onClick={onRemove}
        disabled={isRemoved || (!image && !preview)}
      >
        Remove image
      </button>
    </div>
  )

  return (
    <main className="profile-edit-page">
      <div className="profile-edit-container">
        <header className="profile-edit-header">
          <div>
            <span className="vibespace-eyebrow">BEYOND YOUR BUBBLE</span>
            <h1>Edit your VibeSpace</h1>
            <p>Update how the BYB community sees you.</p>
          </div>

          <Link to="/home" className="profile-edit-back">
            Cancel
          </Link>
        </header>

        <form onSubmit={handleSubmit} className="profile-edit-form">
          {error && <div className="profile-edit-message error">{error}</div>}
          {success && <div className="profile-edit-message success">{success}</div>}

          <section className="profile-edit-section">
            <h2>Profile images</h2>

            <div className="profile-edit-image-grid">
              <ImagePreview
                title="Profile picture"
                image={profile.profile_picture}
                preview={profilePreview}
                onChange={(event) => handleImageChange(event, 'profile_picture')}
                onRemove={() => {
                  setRemoveProfilePicture(true)
                  setProfilePicture(null)
                  setProfilePreview('')
                }}
                isRemoved={removeProfilePicture}
              />

              <ImagePreview
                title="Cover image"
                image={profile.cover_image}
                preview={coverPreview}
                onChange={(event) => handleImageChange(event, 'cover_image')}
                onRemove={() => {
                  setRemoveCoverImage(true)
                  setCoverImage(null)
                  setCoverPreview('')
                }}
                isRemoved={removeCoverImage}
              />
            </div>
          </section>

          <section className="profile-edit-section">
            <h2>Personal information</h2>

            <div className="profile-edit-grid">
              <label>
                First name *
                <input
                  required
                  value={form.first_name}
                  onChange={(event) => updateField('first_name', event.target.value)}
                />
              </label>

              <label>
                Last name *
                <input
                  required
                  value={form.last_name}
                  onChange={(event) => updateField('last_name', event.target.value)}
                />
              </label>

              <label>
                BYB signature
                <input
                  value={form.byb_signature || ''}
                  onChange={(event) => updateField('byb_signature', event.target.value)}
                  placeholder="A short line that represents you"
                />
              </label>

              <label>
                City
                <input
                  value={form.city}
                  onChange={(event) => updateField('city', event.target.value)}
                />
              </label>
            </div>

            <label className="profile-edit-full-field">
              Bio
              <textarea
                rows={4}
                value={form.bio}
                onChange={(event) => updateField('bio', event.target.value)}
                placeholder="Tell the BYB community about yourself..."
              />
            </label>
          </section>

          <section className="profile-edit-section">
            <h2>Profile type</h2>

            <label>
              I am a
              <select
                value={form.profile_type}
                onChange={(event) => updateField(
                  'profile_type',
                  event.target.value as 'student' | 'professional'
                )}
              >
                <option value="student">Student</option>
                <option value="professional">Professional</option>
              </select>
            </label>

            {form.profile_type === 'student' ? (
              <div className="profile-edit-grid">
                <label>
                  Institution
                  <input
                    value={form.institution}
                    onChange={(event) => updateField('institution', event.target.value)}
                  />
                </label>

                <label>
                  Course
                  <input
                    value={form.course}
                    onChange={(event) => updateField('course', event.target.value)}
                  />
                </label>

                <label>
                  Field of study
                  <input
                    value={form.field_of_study}
                    onChange={(event) => updateField('field_of_study', event.target.value)}
                  />
                </label>

                <label>
                  Academic year
                  <input
                    value={form.academic_year}
                    onChange={(event) => updateField('academic_year', event.target.value)}
                  />
                </label>

                <label>
                  Graduation year
                  <input
                    type="number"
                    value={form.graduation_year ?? ''}
                    onChange={(event) => updateField(
                      'graduation_year',
                      event.target.value ? Number(event.target.value) : null
                    )}
                  />
                </label>
              </div>
            ) : (
              <div className="profile-edit-grid">
                <label>
                  Organisation
                  <input
                    value={form.current_organization}
                    onChange={(event) => updateField('current_organization', event.target.value)}
                  />
                </label>

                <label>
                  Job title
                  <input
                    value={form.job_title}
                    onChange={(event) => updateField('job_title', event.target.value)}
                  />
                </label>

                <label>
                  Industry
                  <input
                    value={form.industry}
                    onChange={(event) => updateField('industry', event.target.value)}
                  />
                </label>

                <label>
                  Experience (years)
                  <input
                    type="number"
                    min="0"
                    value={form.experience_years ?? ''}
                    onChange={(event) => updateField(
                      'experience_years',
                      event.target.value ? Number(event.target.value) : null
                    )}
                  />
                </label>
              </div>
            )}
          </section>

          <section className="profile-edit-section">
            <h2>Interests and skills</h2>

            <label className="profile-edit-full-field">
              Interests
              <textarea
                rows={2}
                value={interestsText}
                onChange={(event) => setInterestsText(event.target.value)}
                placeholder="Technology, music, entrepreneurship"
              />
              <small>Separate each interest with a comma.</small>
            </label>

            <label className="profile-edit-full-field">
              Skills
              <textarea
                rows={2}
                value={skillsText}
                onChange={(event) => setSkillsText(event.target.value)}
                placeholder="Python, React, UI Design"
              />
              <small>Separate each skill with a comma.</small>
            </label>
          </section>

          <section className="profile-edit-section">
            <h2>Online presence</h2>

            <div className="profile-edit-grid">
              <label>
                LinkedIn URL
                <input
                  type="url"
                  value={form.linkedin_url}
                  onChange={(event) => updateField('linkedin_url', event.target.value)}
                />
              </label>

              <label>
                GitHub URL
                <input
                  type="url"
                  value={form.github_url}
                  onChange={(event) => updateField('github_url', event.target.value)}
                />
              </label>

              <label>
                Website URL
                <input
                  type="url"
                  value={form.website_url}
                  onChange={(event) => updateField('website_url', event.target.value)}
                />
              </label>
            </div>
          </section>

          <section className="profile-edit-section">
            <h2>Profile visibility</h2>

            <label>
              Who can view your profile?
              <select
                value={form.visibility}
                onChange={(event) => updateField(
                  'visibility',
                  event.target.value as 'public' | 'private'
                )}
              >
                <option value="public">Public</option>
                <option value="private">Private</option>
              </select>
            </label>
          </section>

          <div className="profile-edit-actions">
            <Link to="/home" className="profile-edit-cancel">
              Cancel
            </Link>

            <button type="submit" disabled={saving}>
              {saving ? 'Saving changes...' : 'Save changes'}
            </button>
          </div>
        </form>
      </div>
    </main>
  )
}
