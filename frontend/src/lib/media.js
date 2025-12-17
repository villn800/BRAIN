import { buildAssetUrl } from './assets'

function looksLikeMp4(path) {
  if (!path) {
    return false
  }
  return /\.mp4(\?|$)/i.test(path)
}

export function isVideoItem(item) {
  if (!item) {
    return false
  }
  if (item.extra?.media_kind === 'video') {
    return true
  }
  if (looksLikeMp4(item.extra?.video_url)) {
    return true
  }
  return looksLikeMp4(item.file_path)
}

export function getVideoSrc(item) {
  if (!item) {
    return null
  }
  if (looksLikeMp4(item.file_path)) {
    return buildAssetUrl(item.file_path)
  }
  if (looksLikeMp4(item.extra?.video_url)) {
    return item.extra.video_url
  }
  return null
}

export function getPosterSrc(item) {
  if (!item) {
    return null
  }
  if (item.thumbnail_path) {
    return buildAssetUrl(item.thumbnail_path)
  }
  if (item.extra?.poster_path) {
    return buildAssetUrl(item.extra.poster_path)
  }
  return null
}
