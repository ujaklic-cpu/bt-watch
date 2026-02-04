package net.jaklic.btwatch

import com.squareup.moshi.JsonClass
import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import retrofit2.http.Body
import retrofit2.http.POST

@JsonClass(generateAdapter = true)
data class AdvertPayload(
    val host: String,
    val location: String,
    val address: String,
    val name: String?,
    val rssi: Int,
    val ts: Double
)

interface IngestApi {
    @POST("ingest")
    suspend fun send(@Body payload: AdvertPayload)
}

fun buildApi(baseUrl: String): IngestApi {
    val client = OkHttpClient.Builder().build()
    val retrofit = Retrofit.Builder()
        .baseUrl(if (baseUrl.endsWith("/")) baseUrl else "$baseUrl/")
        .client(client)
        .addConverterFactory(MoshiConverterFactory.create())
        .build()
    return retrofit.create(IngestApi::class.java)
}
