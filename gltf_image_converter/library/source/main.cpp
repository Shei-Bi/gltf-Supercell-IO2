#define WK_DLL_EXPORT 1

#include "texture/texture.h"
#include "core/stb/stb.h"
#include "core/preprocessor/api.h"

namespace fs = std::filesystem;

extern "C" {
	WORKSHOP_API int __cdecl decompress_sctx(const char* path, void** data_out, unsigned int* data_out_len, unsigned int* width_out, unsigned int* height_out, const char** error_out) {
		auto stream = wk::CreateRef<wk::InputFileStream>(fs::path(path));
		auto texture = wk::CreateRef<sc::texture::SupercellTexture>(*stream);
		texture->read_data();

		wk::Image::PixelDepth depth;
		wk::Image::ColorSpace space;
		try
		{
			depth = texture->depth();
			space = texture->colorspace();
		}
		catch (const wk::Exception&)
		{
			*error_out = "Pixel type is not supported for decoding";
			return -1;
		}

		wk::Ref<wk::RawImage> image;

		if (texture->is_compressed())
		{
			image = wk::CreateRef<wk::RawImage>(texture->width(), texture->height(), depth, space);
			wk::SharedMemoryStream compressed_stream(image->data(), image->data_length());
			texture->decompress_data(compressed_stream);
		}
		else
		{
			image = wk::CreateRef<wk::RawImage>(
				texture->data(),
				texture->width(), texture->height(), depth, space
			);
		}
		*data_out = wk::Memory::allocate(image->data_length());
		memcpy(*data_out, image->data(), image->data_length());
		*data_out_len = static_cast<unsigned int>(image->data_length());
		*width_out = image->width();
		*height_out = image->height();
		return 0;
	}

	WORKSHOP_API int __cdecl free_decompressed_data(void* data) {
		wk::Memory::free(data);
		return 0;
	}
}