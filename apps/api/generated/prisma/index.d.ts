
/**
 * Client
**/

import * as runtime from './runtime/library.js';
import $Types = runtime.Types // general types
import $Public = runtime.Types.Public
import $Utils = runtime.Types.Utils
import $Extensions = runtime.Types.Extensions
import $Result = runtime.Types.Result

export type PrismaPromise<T> = $Public.PrismaPromise<T>


/**
 * Model User
 * 
 */
export type User = $Result.DefaultSelection<Prisma.$UserPayload>
/**
 * Model Simulation
 * 
 */
export type Simulation = $Result.DefaultSelection<Prisma.$SimulationPayload>
/**
 * Model BiasDetectionResult
 * 
 */
export type BiasDetectionResult = $Result.DefaultSelection<Prisma.$BiasDetectionResultPayload>
/**
 * Model FairnessAssessment
 * 
 */
export type FairnessAssessment = $Result.DefaultSelection<Prisma.$FairnessAssessmentPayload>
/**
 * Model ExplainabilityAnalysis
 * 
 */
export type ExplainabilityAnalysis = $Result.DefaultSelection<Prisma.$ExplainabilityAnalysisPayload>
/**
 * Model ComplianceRecord
 * 
 */
export type ComplianceRecord = $Result.DefaultSelection<Prisma.$ComplianceRecordPayload>
/**
 * Model RiskAssessment
 * 
 */
export type RiskAssessment = $Result.DefaultSelection<Prisma.$RiskAssessmentPayload>
/**
 * Model AuditLog
 * 
 */
export type AuditLog = $Result.DefaultSelection<Prisma.$AuditLogPayload>

/**
 * Enums
 */
export namespace $Enums {
  export const SimulationStatus: {
  DRAFT: 'DRAFT',
  IN_PROGRESS: 'IN_PROGRESS',
  COMPLETED: 'COMPLETED',
  FAILED: 'FAILED',
  ARCHIVED: 'ARCHIVED'
};

export type SimulationStatus = (typeof SimulationStatus)[keyof typeof SimulationStatus]

}

export type SimulationStatus = $Enums.SimulationStatus

export const SimulationStatus: typeof $Enums.SimulationStatus

/**
 * ##  Prisma Client ʲˢ
 *
 * Type-safe database client for TypeScript & Node.js
 * @example
 * ```
 * const prisma = new PrismaClient()
 * // Fetch zero or more Users
 * const users = await prisma.user.findMany()
 * ```
 *
 *
 * Read more in our [docs](https://www.prisma.io/docs/reference/tools-and-interfaces/prisma-client).
 */
export class PrismaClient<
  ClientOptions extends Prisma.PrismaClientOptions = Prisma.PrismaClientOptions,
  U = 'log' extends keyof ClientOptions ? ClientOptions['log'] extends Array<Prisma.LogLevel | Prisma.LogDefinition> ? Prisma.GetEvents<ClientOptions['log']> : never : never,
  ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs
> {
  [K: symbol]: { types: Prisma.TypeMap<ExtArgs>['other'] }

    /**
   * ##  Prisma Client ʲˢ
   *
   * Type-safe database client for TypeScript & Node.js
   * @example
   * ```
   * const prisma = new PrismaClient()
   * // Fetch zero or more Users
   * const users = await prisma.user.findMany()
   * ```
   *
   *
   * Read more in our [docs](https://www.prisma.io/docs/reference/tools-and-interfaces/prisma-client).
   */

  constructor(optionsArg ?: Prisma.Subset<ClientOptions, Prisma.PrismaClientOptions>);
  $on<V extends U>(eventType: V, callback: (event: V extends 'query' ? Prisma.QueryEvent : Prisma.LogEvent) => void): PrismaClient;

  /**
   * Connect with the database
   */
  $connect(): $Utils.JsPromise<void>;

  /**
   * Disconnect from the database
   */
  $disconnect(): $Utils.JsPromise<void>;

  /**
   * Add a middleware
   * @deprecated since 4.16.0. For new code, prefer client extensions instead.
   * @see https://pris.ly/d/extensions
   */
  $use(cb: Prisma.Middleware): void

/**
   * Executes a prepared raw query and returns the number of affected rows.
   * @example
   * ```
   * const result = await prisma.$executeRaw`UPDATE User SET cool = ${true} WHERE email = ${'user@email.com'};`
   * ```
   *
   * Read more in our [docs](https://www.prisma.io/docs/reference/tools-and-interfaces/prisma-client/raw-database-access).
   */
  $executeRaw<T = unknown>(query: TemplateStringsArray | Prisma.Sql, ...values: any[]): Prisma.PrismaPromise<number>;

  /**
   * Executes a raw query and returns the number of affected rows.
   * Susceptible to SQL injections, see documentation.
   * @example
   * ```
   * const result = await prisma.$executeRawUnsafe('UPDATE User SET cool = $1 WHERE email = $2 ;', true, 'user@email.com')
   * ```
   *
   * Read more in our [docs](https://www.prisma.io/docs/reference/tools-and-interfaces/prisma-client/raw-database-access).
   */
  $executeRawUnsafe<T = unknown>(query: string, ...values: any[]): Prisma.PrismaPromise<number>;

  /**
   * Performs a prepared raw query and returns the `SELECT` data.
   * @example
   * ```
   * const result = await prisma.$queryRaw`SELECT * FROM User WHERE id = ${1} OR email = ${'user@email.com'};`
   * ```
   *
   * Read more in our [docs](https://www.prisma.io/docs/reference/tools-and-interfaces/prisma-client/raw-database-access).
   */
  $queryRaw<T = unknown>(query: TemplateStringsArray | Prisma.Sql, ...values: any[]): Prisma.PrismaPromise<T>;

  /**
   * Performs a raw query and returns the `SELECT` data.
   * Susceptible to SQL injections, see documentation.
   * @example
   * ```
   * const result = await prisma.$queryRawUnsafe('SELECT * FROM User WHERE id = $1 OR email = $2;', 1, 'user@email.com')
   * ```
   *
   * Read more in our [docs](https://www.prisma.io/docs/reference/tools-and-interfaces/prisma-client/raw-database-access).
   */
  $queryRawUnsafe<T = unknown>(query: string, ...values: any[]): Prisma.PrismaPromise<T>;


  /**
   * Allows the running of a sequence of read/write operations that are guaranteed to either succeed or fail as a whole.
   * @example
   * ```
   * const [george, bob, alice] = await prisma.$transaction([
   *   prisma.user.create({ data: { name: 'George' } }),
   *   prisma.user.create({ data: { name: 'Bob' } }),
   *   prisma.user.create({ data: { name: 'Alice' } }),
   * ])
   * ```
   * 
   * Read more in our [docs](https://www.prisma.io/docs/concepts/components/prisma-client/transactions).
   */
  $transaction<P extends Prisma.PrismaPromise<any>[]>(arg: [...P], options?: { isolationLevel?: Prisma.TransactionIsolationLevel }): $Utils.JsPromise<runtime.Types.Utils.UnwrapTuple<P>>

  $transaction<R>(fn: (prisma: Omit<PrismaClient, runtime.ITXClientDenyList>) => $Utils.JsPromise<R>, options?: { maxWait?: number, timeout?: number, isolationLevel?: Prisma.TransactionIsolationLevel }): $Utils.JsPromise<R>


  $extends: $Extensions.ExtendsHook<"extends", Prisma.TypeMapCb<ClientOptions>, ExtArgs, $Utils.Call<Prisma.TypeMapCb<ClientOptions>, {
    extArgs: ExtArgs
  }>>

      /**
   * `prisma.user`: Exposes CRUD operations for the **User** model.
    * Example usage:
    * ```ts
    * // Fetch zero or more Users
    * const users = await prisma.user.findMany()
    * ```
    */
  get user(): Prisma.UserDelegate<ExtArgs, ClientOptions>;

  /**
   * `prisma.simulation`: Exposes CRUD operations for the **Simulation** model.
    * Example usage:
    * ```ts
    * // Fetch zero or more Simulations
    * const simulations = await prisma.simulation.findMany()
    * ```
    */
  get simulation(): Prisma.SimulationDelegate<ExtArgs, ClientOptions>;

  /**
   * `prisma.biasDetectionResult`: Exposes CRUD operations for the **BiasDetectionResult** model.
    * Example usage:
    * ```ts
    * // Fetch zero or more BiasDetectionResults
    * const biasDetectionResults = await prisma.biasDetectionResult.findMany()
    * ```
    */
  get biasDetectionResult(): Prisma.BiasDetectionResultDelegate<ExtArgs, ClientOptions>;

  /**
   * `prisma.fairnessAssessment`: Exposes CRUD operations for the **FairnessAssessment** model.
    * Example usage:
    * ```ts
    * // Fetch zero or more FairnessAssessments
    * const fairnessAssessments = await prisma.fairnessAssessment.findMany()
    * ```
    */
  get fairnessAssessment(): Prisma.FairnessAssessmentDelegate<ExtArgs, ClientOptions>;

  /**
   * `prisma.explainabilityAnalysis`: Exposes CRUD operations for the **ExplainabilityAnalysis** model.
    * Example usage:
    * ```ts
    * // Fetch zero or more ExplainabilityAnalyses
    * const explainabilityAnalyses = await prisma.explainabilityAnalysis.findMany()
    * ```
    */
  get explainabilityAnalysis(): Prisma.ExplainabilityAnalysisDelegate<ExtArgs, ClientOptions>;

  /**
   * `prisma.complianceRecord`: Exposes CRUD operations for the **ComplianceRecord** model.
    * Example usage:
    * ```ts
    * // Fetch zero or more ComplianceRecords
    * const complianceRecords = await prisma.complianceRecord.findMany()
    * ```
    */
  get complianceRecord(): Prisma.ComplianceRecordDelegate<ExtArgs, ClientOptions>;

  /**
   * `prisma.riskAssessment`: Exposes CRUD operations for the **RiskAssessment** model.
    * Example usage:
    * ```ts
    * // Fetch zero or more RiskAssessments
    * const riskAssessments = await prisma.riskAssessment.findMany()
    * ```
    */
  get riskAssessment(): Prisma.RiskAssessmentDelegate<ExtArgs, ClientOptions>;

  /**
   * `prisma.auditLog`: Exposes CRUD operations for the **AuditLog** model.
    * Example usage:
    * ```ts
    * // Fetch zero or more AuditLogs
    * const auditLogs = await prisma.auditLog.findMany()
    * ```
    */
  get auditLog(): Prisma.AuditLogDelegate<ExtArgs, ClientOptions>;
}

export namespace Prisma {
  export import DMMF = runtime.DMMF

  export type PrismaPromise<T> = $Public.PrismaPromise<T>

  /**
   * Validator
   */
  export import validator = runtime.Public.validator

  /**
   * Prisma Errors
   */
  export import PrismaClientKnownRequestError = runtime.PrismaClientKnownRequestError
  export import PrismaClientUnknownRequestError = runtime.PrismaClientUnknownRequestError
  export import PrismaClientRustPanicError = runtime.PrismaClientRustPanicError
  export import PrismaClientInitializationError = runtime.PrismaClientInitializationError
  export import PrismaClientValidationError = runtime.PrismaClientValidationError

  /**
   * Re-export of sql-template-tag
   */
  export import sql = runtime.sqltag
  export import empty = runtime.empty
  export import join = runtime.join
  export import raw = runtime.raw
  export import Sql = runtime.Sql



  /**
   * Decimal.js
   */
  export import Decimal = runtime.Decimal

  export type DecimalJsLike = runtime.DecimalJsLike

  /**
   * Metrics
   */
  export type Metrics = runtime.Metrics
  export type Metric<T> = runtime.Metric<T>
  export type MetricHistogram = runtime.MetricHistogram
  export type MetricHistogramBucket = runtime.MetricHistogramBucket

  /**
  * Extensions
  */
  export import Extension = $Extensions.UserArgs
  export import getExtensionContext = runtime.Extensions.getExtensionContext
  export import Args = $Public.Args
  export import Payload = $Public.Payload
  export import Result = $Public.Result
  export import Exact = $Public.Exact

  /**
   * Prisma Client JS version: 6.12.0
   * Query Engine version: 8047c96bbd92db98a2abc7c9323ce77c02c89dbc
   */
  export type PrismaVersion = {
    client: string
  }

  export const prismaVersion: PrismaVersion

  /**
   * Utility Types
   */


  export import JsonObject = runtime.JsonObject
  export import JsonArray = runtime.JsonArray
  export import JsonValue = runtime.JsonValue
  export import InputJsonObject = runtime.InputJsonObject
  export import InputJsonArray = runtime.InputJsonArray
  export import InputJsonValue = runtime.InputJsonValue

  /**
   * Types of the values used to represent different kinds of `null` values when working with JSON fields.
   *
   * @see https://www.prisma.io/docs/concepts/components/prisma-client/working-with-fields/working-with-json-fields#filtering-on-a-json-field
   */
  namespace NullTypes {
    /**
    * Type of `Prisma.DbNull`.
    *
    * You cannot use other instances of this class. Please use the `Prisma.DbNull` value.
    *
    * @see https://www.prisma.io/docs/concepts/components/prisma-client/working-with-fields/working-with-json-fields#filtering-on-a-json-field
    */
    class DbNull {
      private DbNull: never
      private constructor()
    }

    /**
    * Type of `Prisma.JsonNull`.
    *
    * You cannot use other instances of this class. Please use the `Prisma.JsonNull` value.
    *
    * @see https://www.prisma.io/docs/concepts/components/prisma-client/working-with-fields/working-with-json-fields#filtering-on-a-json-field
    */
    class JsonNull {
      private JsonNull: never
      private constructor()
    }

    /**
    * Type of `Prisma.AnyNull`.
    *
    * You cannot use other instances of this class. Please use the `Prisma.AnyNull` value.
    *
    * @see https://www.prisma.io/docs/concepts/components/prisma-client/working-with-fields/working-with-json-fields#filtering-on-a-json-field
    */
    class AnyNull {
      private AnyNull: never
      private constructor()
    }
  }

  /**
   * Helper for filtering JSON entries that have `null` on the database (empty on the db)
   *
   * @see https://www.prisma.io/docs/concepts/components/prisma-client/working-with-fields/working-with-json-fields#filtering-on-a-json-field
   */
  export const DbNull: NullTypes.DbNull

  /**
   * Helper for filtering JSON entries that have JSON `null` values (not empty on the db)
   *
   * @see https://www.prisma.io/docs/concepts/components/prisma-client/working-with-fields/working-with-json-fields#filtering-on-a-json-field
   */
  export const JsonNull: NullTypes.JsonNull

  /**
   * Helper for filtering JSON entries that are `Prisma.DbNull` or `Prisma.JsonNull`
   *
   * @see https://www.prisma.io/docs/concepts/components/prisma-client/working-with-fields/working-with-json-fields#filtering-on-a-json-field
   */
  export const AnyNull: NullTypes.AnyNull

  type SelectAndInclude = {
    select: any
    include: any
  }

  type SelectAndOmit = {
    select: any
    omit: any
  }

  /**
   * Get the type of the value, that the Promise holds.
   */
  export type PromiseType<T extends PromiseLike<any>> = T extends PromiseLike<infer U> ? U : T;

  /**
   * Get the return type of a function which returns a Promise.
   */
  export type PromiseReturnType<T extends (...args: any) => $Utils.JsPromise<any>> = PromiseType<ReturnType<T>>

  /**
   * From T, pick a set of properties whose keys are in the union K
   */
  type Prisma__Pick<T, K extends keyof T> = {
      [P in K]: T[P];
  };


  export type Enumerable<T> = T | Array<T>;

  export type RequiredKeys<T> = {
    [K in keyof T]-?: {} extends Prisma__Pick<T, K> ? never : K
  }[keyof T]

  export type TruthyKeys<T> = keyof {
    [K in keyof T as T[K] extends false | undefined | null ? never : K]: K
  }

  export type TrueKeys<T> = TruthyKeys<Prisma__Pick<T, RequiredKeys<T>>>

  /**
   * Subset
   * @desc From `T` pick properties that exist in `U`. Simple version of Intersection
   */
  export type Subset<T, U> = {
    [key in keyof T]: key extends keyof U ? T[key] : never;
  };

  /**
   * SelectSubset
   * @desc From `T` pick properties that exist in `U`. Simple version of Intersection.
   * Additionally, it validates, if both select and include are present. If the case, it errors.
   */
  export type SelectSubset<T, U> = {
    [key in keyof T]: key extends keyof U ? T[key] : never
  } &
    (T extends SelectAndInclude
      ? 'Please either choose `select` or `include`.'
      : T extends SelectAndOmit
        ? 'Please either choose `select` or `omit`.'
        : {})

  /**
   * Subset + Intersection
   * @desc From `T` pick properties that exist in `U` and intersect `K`
   */
  export type SubsetIntersection<T, U, K> = {
    [key in keyof T]: key extends keyof U ? T[key] : never
  } &
    K

  type Without<T, U> = { [P in Exclude<keyof T, keyof U>]?: never };

  /**
   * XOR is needed to have a real mutually exclusive union type
   * https://stackoverflow.com/questions/42123407/does-typescript-support-mutually-exclusive-types
   */
  type XOR<T, U> =
    T extends object ?
    U extends object ?
      (Without<T, U> & U) | (Without<U, T> & T)
    : U : T


  /**
   * Is T a Record?
   */
  type IsObject<T extends any> = T extends Array<any>
  ? False
  : T extends Date
  ? False
  : T extends Uint8Array
  ? False
  : T extends BigInt
  ? False
  : T extends object
  ? True
  : False


  /**
   * If it's T[], return T
   */
  export type UnEnumerate<T extends unknown> = T extends Array<infer U> ? U : T

  /**
   * From ts-toolbelt
   */

  type __Either<O extends object, K extends Key> = Omit<O, K> &
    {
      // Merge all but K
      [P in K]: Prisma__Pick<O, P & keyof O> // With K possibilities
    }[K]

  type EitherStrict<O extends object, K extends Key> = Strict<__Either<O, K>>

  type EitherLoose<O extends object, K extends Key> = ComputeRaw<__Either<O, K>>

  type _Either<
    O extends object,
    K extends Key,
    strict extends Boolean
  > = {
    1: EitherStrict<O, K>
    0: EitherLoose<O, K>
  }[strict]

  type Either<
    O extends object,
    K extends Key,
    strict extends Boolean = 1
  > = O extends unknown ? _Either<O, K, strict> : never

  export type Union = any

  type PatchUndefined<O extends object, O1 extends object> = {
    [K in keyof O]: O[K] extends undefined ? At<O1, K> : O[K]
  } & {}

  /** Helper Types for "Merge" **/
  export type IntersectOf<U extends Union> = (
    U extends unknown ? (k: U) => void : never
  ) extends (k: infer I) => void
    ? I
    : never

  export type Overwrite<O extends object, O1 extends object> = {
      [K in keyof O]: K extends keyof O1 ? O1[K] : O[K];
  } & {};

  type _Merge<U extends object> = IntersectOf<Overwrite<U, {
      [K in keyof U]-?: At<U, K>;
  }>>;

  type Key = string | number | symbol;
  type AtBasic<O extends object, K extends Key> = K extends keyof O ? O[K] : never;
  type AtStrict<O extends object, K extends Key> = O[K & keyof O];
  type AtLoose<O extends object, K extends Key> = O extends unknown ? AtStrict<O, K> : never;
  export type At<O extends object, K extends Key, strict extends Boolean = 1> = {
      1: AtStrict<O, K>;
      0: AtLoose<O, K>;
  }[strict];

  export type ComputeRaw<A extends any> = A extends Function ? A : {
    [K in keyof A]: A[K];
  } & {};

  export type OptionalFlat<O> = {
    [K in keyof O]?: O[K];
  } & {};

  type _Record<K extends keyof any, T> = {
    [P in K]: T;
  };

  // cause typescript not to expand types and preserve names
  type NoExpand<T> = T extends unknown ? T : never;

  // this type assumes the passed object is entirely optional
  type AtLeast<O extends object, K extends string> = NoExpand<
    O extends unknown
    ? | (K extends keyof O ? { [P in K]: O[P] } & O : O)
      | {[P in keyof O as P extends K ? P : never]-?: O[P]} & O
    : never>;

  type _Strict<U, _U = U> = U extends unknown ? U & OptionalFlat<_Record<Exclude<Keys<_U>, keyof U>, never>> : never;

  export type Strict<U extends object> = ComputeRaw<_Strict<U>>;
  /** End Helper Types for "Merge" **/

  export type Merge<U extends object> = ComputeRaw<_Merge<Strict<U>>>;

  /**
  A [[Boolean]]
  */
  export type Boolean = True | False

  // /**
  // 1
  // */
  export type True = 1

  /**
  0
  */
  export type False = 0

  export type Not<B extends Boolean> = {
    0: 1
    1: 0
  }[B]

  export type Extends<A1 extends any, A2 extends any> = [A1] extends [never]
    ? 0 // anything `never` is false
    : A1 extends A2
    ? 1
    : 0

  export type Has<U extends Union, U1 extends Union> = Not<
    Extends<Exclude<U1, U>, U1>
  >

  export type Or<B1 extends Boolean, B2 extends Boolean> = {
    0: {
      0: 0
      1: 1
    }
    1: {
      0: 1
      1: 1
    }
  }[B1][B2]

  export type Keys<U extends Union> = U extends unknown ? keyof U : never

  type Cast<A, B> = A extends B ? A : B;

  export const type: unique symbol;



  /**
   * Used by group by
   */

  export type GetScalarType<T, O> = O extends object ? {
    [P in keyof T]: P extends keyof O
      ? O[P]
      : never
  } : never

  type FieldPaths<
    T,
    U = Omit<T, '_avg' | '_sum' | '_count' | '_min' | '_max'>
  > = IsObject<T> extends True ? U : T

  type GetHavingFields<T> = {
    [K in keyof T]: Or<
      Or<Extends<'OR', K>, Extends<'AND', K>>,
      Extends<'NOT', K>
    > extends True
      ? // infer is only needed to not hit TS limit
        // based on the brilliant idea of Pierre-Antoine Mills
        // https://github.com/microsoft/TypeScript/issues/30188#issuecomment-478938437
        T[K] extends infer TK
        ? GetHavingFields<UnEnumerate<TK> extends object ? Merge<UnEnumerate<TK>> : never>
        : never
      : {} extends FieldPaths<T[K]>
      ? never
      : K
  }[keyof T]

  /**
   * Convert tuple to union
   */
  type _TupleToUnion<T> = T extends (infer E)[] ? E : never
  type TupleToUnion<K extends readonly any[]> = _TupleToUnion<K>
  type MaybeTupleToUnion<T> = T extends any[] ? TupleToUnion<T> : T

  /**
   * Like `Pick`, but additionally can also accept an array of keys
   */
  type PickEnumerable<T, K extends Enumerable<keyof T> | keyof T> = Prisma__Pick<T, MaybeTupleToUnion<K>>

  /**
   * Exclude all keys with underscores
   */
  type ExcludeUnderscoreKeys<T extends string> = T extends `_${string}` ? never : T


  export type FieldRef<Model, FieldType> = runtime.FieldRef<Model, FieldType>

  type FieldRefInputType<Model, FieldType> = Model extends never ? never : FieldRef<Model, FieldType>


  export const ModelName: {
    User: 'User',
    Simulation: 'Simulation',
    BiasDetectionResult: 'BiasDetectionResult',
    FairnessAssessment: 'FairnessAssessment',
    ExplainabilityAnalysis: 'ExplainabilityAnalysis',
    ComplianceRecord: 'ComplianceRecord',
    RiskAssessment: 'RiskAssessment',
    AuditLog: 'AuditLog'
  };

  export type ModelName = (typeof ModelName)[keyof typeof ModelName]


  export type Datasources = {
    db?: Datasource
  }

  interface TypeMapCb<ClientOptions = {}> extends $Utils.Fn<{extArgs: $Extensions.InternalArgs }, $Utils.Record<string, any>> {
    returns: Prisma.TypeMap<this['params']['extArgs'], ClientOptions extends { omit: infer OmitOptions } ? OmitOptions : {}>
  }

  export type TypeMap<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> = {
    globalOmitOptions: {
      omit: GlobalOmitOptions
    }
    meta: {
      modelProps: "user" | "simulation" | "biasDetectionResult" | "fairnessAssessment" | "explainabilityAnalysis" | "complianceRecord" | "riskAssessment" | "auditLog"
      txIsolationLevel: Prisma.TransactionIsolationLevel
    }
    model: {
      User: {
        payload: Prisma.$UserPayload<ExtArgs>
        fields: Prisma.UserFieldRefs
        operations: {
          findUnique: {
            args: Prisma.UserFindUniqueArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload> | null
          }
          findUniqueOrThrow: {
            args: Prisma.UserFindUniqueOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload>
          }
          findFirst: {
            args: Prisma.UserFindFirstArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload> | null
          }
          findFirstOrThrow: {
            args: Prisma.UserFindFirstOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload>
          }
          findMany: {
            args: Prisma.UserFindManyArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload>[]
          }
          create: {
            args: Prisma.UserCreateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload>
          }
          createMany: {
            args: Prisma.UserCreateManyArgs<ExtArgs>
            result: BatchPayload
          }
          createManyAndReturn: {
            args: Prisma.UserCreateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload>[]
          }
          delete: {
            args: Prisma.UserDeleteArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload>
          }
          update: {
            args: Prisma.UserUpdateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload>
          }
          deleteMany: {
            args: Prisma.UserDeleteManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateMany: {
            args: Prisma.UserUpdateManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateManyAndReturn: {
            args: Prisma.UserUpdateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload>[]
          }
          upsert: {
            args: Prisma.UserUpsertArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload>
          }
          aggregate: {
            args: Prisma.UserAggregateArgs<ExtArgs>
            result: $Utils.Optional<AggregateUser>
          }
          groupBy: {
            args: Prisma.UserGroupByArgs<ExtArgs>
            result: $Utils.Optional<UserGroupByOutputType>[]
          }
          count: {
            args: Prisma.UserCountArgs<ExtArgs>
            result: $Utils.Optional<UserCountAggregateOutputType> | number
          }
        }
      }
      Simulation: {
        payload: Prisma.$SimulationPayload<ExtArgs>
        fields: Prisma.SimulationFieldRefs
        operations: {
          findUnique: {
            args: Prisma.SimulationFindUniqueArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SimulationPayload> | null
          }
          findUniqueOrThrow: {
            args: Prisma.SimulationFindUniqueOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SimulationPayload>
          }
          findFirst: {
            args: Prisma.SimulationFindFirstArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SimulationPayload> | null
          }
          findFirstOrThrow: {
            args: Prisma.SimulationFindFirstOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SimulationPayload>
          }
          findMany: {
            args: Prisma.SimulationFindManyArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SimulationPayload>[]
          }
          create: {
            args: Prisma.SimulationCreateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SimulationPayload>
          }
          createMany: {
            args: Prisma.SimulationCreateManyArgs<ExtArgs>
            result: BatchPayload
          }
          createManyAndReturn: {
            args: Prisma.SimulationCreateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SimulationPayload>[]
          }
          delete: {
            args: Prisma.SimulationDeleteArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SimulationPayload>
          }
          update: {
            args: Prisma.SimulationUpdateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SimulationPayload>
          }
          deleteMany: {
            args: Prisma.SimulationDeleteManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateMany: {
            args: Prisma.SimulationUpdateManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateManyAndReturn: {
            args: Prisma.SimulationUpdateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SimulationPayload>[]
          }
          upsert: {
            args: Prisma.SimulationUpsertArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SimulationPayload>
          }
          aggregate: {
            args: Prisma.SimulationAggregateArgs<ExtArgs>
            result: $Utils.Optional<AggregateSimulation>
          }
          groupBy: {
            args: Prisma.SimulationGroupByArgs<ExtArgs>
            result: $Utils.Optional<SimulationGroupByOutputType>[]
          }
          count: {
            args: Prisma.SimulationCountArgs<ExtArgs>
            result: $Utils.Optional<SimulationCountAggregateOutputType> | number
          }
        }
      }
      BiasDetectionResult: {
        payload: Prisma.$BiasDetectionResultPayload<ExtArgs>
        fields: Prisma.BiasDetectionResultFieldRefs
        operations: {
          findUnique: {
            args: Prisma.BiasDetectionResultFindUniqueArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$BiasDetectionResultPayload> | null
          }
          findUniqueOrThrow: {
            args: Prisma.BiasDetectionResultFindUniqueOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$BiasDetectionResultPayload>
          }
          findFirst: {
            args: Prisma.BiasDetectionResultFindFirstArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$BiasDetectionResultPayload> | null
          }
          findFirstOrThrow: {
            args: Prisma.BiasDetectionResultFindFirstOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$BiasDetectionResultPayload>
          }
          findMany: {
            args: Prisma.BiasDetectionResultFindManyArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$BiasDetectionResultPayload>[]
          }
          create: {
            args: Prisma.BiasDetectionResultCreateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$BiasDetectionResultPayload>
          }
          createMany: {
            args: Prisma.BiasDetectionResultCreateManyArgs<ExtArgs>
            result: BatchPayload
          }
          createManyAndReturn: {
            args: Prisma.BiasDetectionResultCreateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$BiasDetectionResultPayload>[]
          }
          delete: {
            args: Prisma.BiasDetectionResultDeleteArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$BiasDetectionResultPayload>
          }
          update: {
            args: Prisma.BiasDetectionResultUpdateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$BiasDetectionResultPayload>
          }
          deleteMany: {
            args: Prisma.BiasDetectionResultDeleteManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateMany: {
            args: Prisma.BiasDetectionResultUpdateManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateManyAndReturn: {
            args: Prisma.BiasDetectionResultUpdateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$BiasDetectionResultPayload>[]
          }
          upsert: {
            args: Prisma.BiasDetectionResultUpsertArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$BiasDetectionResultPayload>
          }
          aggregate: {
            args: Prisma.BiasDetectionResultAggregateArgs<ExtArgs>
            result: $Utils.Optional<AggregateBiasDetectionResult>
          }
          groupBy: {
            args: Prisma.BiasDetectionResultGroupByArgs<ExtArgs>
            result: $Utils.Optional<BiasDetectionResultGroupByOutputType>[]
          }
          count: {
            args: Prisma.BiasDetectionResultCountArgs<ExtArgs>
            result: $Utils.Optional<BiasDetectionResultCountAggregateOutputType> | number
          }
        }
      }
      FairnessAssessment: {
        payload: Prisma.$FairnessAssessmentPayload<ExtArgs>
        fields: Prisma.FairnessAssessmentFieldRefs
        operations: {
          findUnique: {
            args: Prisma.FairnessAssessmentFindUniqueArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FairnessAssessmentPayload> | null
          }
          findUniqueOrThrow: {
            args: Prisma.FairnessAssessmentFindUniqueOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FairnessAssessmentPayload>
          }
          findFirst: {
            args: Prisma.FairnessAssessmentFindFirstArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FairnessAssessmentPayload> | null
          }
          findFirstOrThrow: {
            args: Prisma.FairnessAssessmentFindFirstOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FairnessAssessmentPayload>
          }
          findMany: {
            args: Prisma.FairnessAssessmentFindManyArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FairnessAssessmentPayload>[]
          }
          create: {
            args: Prisma.FairnessAssessmentCreateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FairnessAssessmentPayload>
          }
          createMany: {
            args: Prisma.FairnessAssessmentCreateManyArgs<ExtArgs>
            result: BatchPayload
          }
          createManyAndReturn: {
            args: Prisma.FairnessAssessmentCreateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FairnessAssessmentPayload>[]
          }
          delete: {
            args: Prisma.FairnessAssessmentDeleteArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FairnessAssessmentPayload>
          }
          update: {
            args: Prisma.FairnessAssessmentUpdateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FairnessAssessmentPayload>
          }
          deleteMany: {
            args: Prisma.FairnessAssessmentDeleteManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateMany: {
            args: Prisma.FairnessAssessmentUpdateManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateManyAndReturn: {
            args: Prisma.FairnessAssessmentUpdateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FairnessAssessmentPayload>[]
          }
          upsert: {
            args: Prisma.FairnessAssessmentUpsertArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FairnessAssessmentPayload>
          }
          aggregate: {
            args: Prisma.FairnessAssessmentAggregateArgs<ExtArgs>
            result: $Utils.Optional<AggregateFairnessAssessment>
          }
          groupBy: {
            args: Prisma.FairnessAssessmentGroupByArgs<ExtArgs>
            result: $Utils.Optional<FairnessAssessmentGroupByOutputType>[]
          }
          count: {
            args: Prisma.FairnessAssessmentCountArgs<ExtArgs>
            result: $Utils.Optional<FairnessAssessmentCountAggregateOutputType> | number
          }
        }
      }
      ExplainabilityAnalysis: {
        payload: Prisma.$ExplainabilityAnalysisPayload<ExtArgs>
        fields: Prisma.ExplainabilityAnalysisFieldRefs
        operations: {
          findUnique: {
            args: Prisma.ExplainabilityAnalysisFindUniqueArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$ExplainabilityAnalysisPayload> | null
          }
          findUniqueOrThrow: {
            args: Prisma.ExplainabilityAnalysisFindUniqueOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$ExplainabilityAnalysisPayload>
          }
          findFirst: {
            args: Prisma.ExplainabilityAnalysisFindFirstArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$ExplainabilityAnalysisPayload> | null
          }
          findFirstOrThrow: {
            args: Prisma.ExplainabilityAnalysisFindFirstOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$ExplainabilityAnalysisPayload>
          }
          findMany: {
            args: Prisma.ExplainabilityAnalysisFindManyArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$ExplainabilityAnalysisPayload>[]
          }
          create: {
            args: Prisma.ExplainabilityAnalysisCreateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$ExplainabilityAnalysisPayload>
          }
          createMany: {
            args: Prisma.ExplainabilityAnalysisCreateManyArgs<ExtArgs>
            result: BatchPayload
          }
          createManyAndReturn: {
            args: Prisma.ExplainabilityAnalysisCreateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$ExplainabilityAnalysisPayload>[]
          }
          delete: {
            args: Prisma.ExplainabilityAnalysisDeleteArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$ExplainabilityAnalysisPayload>
          }
          update: {
            args: Prisma.ExplainabilityAnalysisUpdateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$ExplainabilityAnalysisPayload>
          }
          deleteMany: {
            args: Prisma.ExplainabilityAnalysisDeleteManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateMany: {
            args: Prisma.ExplainabilityAnalysisUpdateManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateManyAndReturn: {
            args: Prisma.ExplainabilityAnalysisUpdateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$ExplainabilityAnalysisPayload>[]
          }
          upsert: {
            args: Prisma.ExplainabilityAnalysisUpsertArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$ExplainabilityAnalysisPayload>
          }
          aggregate: {
            args: Prisma.ExplainabilityAnalysisAggregateArgs<ExtArgs>
            result: $Utils.Optional<AggregateExplainabilityAnalysis>
          }
          groupBy: {
            args: Prisma.ExplainabilityAnalysisGroupByArgs<ExtArgs>
            result: $Utils.Optional<ExplainabilityAnalysisGroupByOutputType>[]
          }
          count: {
            args: Prisma.ExplainabilityAnalysisCountArgs<ExtArgs>
            result: $Utils.Optional<ExplainabilityAnalysisCountAggregateOutputType> | number
          }
        }
      }
      ComplianceRecord: {
        payload: Prisma.$ComplianceRecordPayload<ExtArgs>
        fields: Prisma.ComplianceRecordFieldRefs
        operations: {
          findUnique: {
            args: Prisma.ComplianceRecordFindUniqueArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$ComplianceRecordPayload> | null
          }
          findUniqueOrThrow: {
            args: Prisma.ComplianceRecordFindUniqueOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$ComplianceRecordPayload>
          }
          findFirst: {
            args: Prisma.ComplianceRecordFindFirstArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$ComplianceRecordPayload> | null
          }
          findFirstOrThrow: {
            args: Prisma.ComplianceRecordFindFirstOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$ComplianceRecordPayload>
          }
          findMany: {
            args: Prisma.ComplianceRecordFindManyArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$ComplianceRecordPayload>[]
          }
          create: {
            args: Prisma.ComplianceRecordCreateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$ComplianceRecordPayload>
          }
          createMany: {
            args: Prisma.ComplianceRecordCreateManyArgs<ExtArgs>
            result: BatchPayload
          }
          createManyAndReturn: {
            args: Prisma.ComplianceRecordCreateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$ComplianceRecordPayload>[]
          }
          delete: {
            args: Prisma.ComplianceRecordDeleteArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$ComplianceRecordPayload>
          }
          update: {
            args: Prisma.ComplianceRecordUpdateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$ComplianceRecordPayload>
          }
          deleteMany: {
            args: Prisma.ComplianceRecordDeleteManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateMany: {
            args: Prisma.ComplianceRecordUpdateManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateManyAndReturn: {
            args: Prisma.ComplianceRecordUpdateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$ComplianceRecordPayload>[]
          }
          upsert: {
            args: Prisma.ComplianceRecordUpsertArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$ComplianceRecordPayload>
          }
          aggregate: {
            args: Prisma.ComplianceRecordAggregateArgs<ExtArgs>
            result: $Utils.Optional<AggregateComplianceRecord>
          }
          groupBy: {
            args: Prisma.ComplianceRecordGroupByArgs<ExtArgs>
            result: $Utils.Optional<ComplianceRecordGroupByOutputType>[]
          }
          count: {
            args: Prisma.ComplianceRecordCountArgs<ExtArgs>
            result: $Utils.Optional<ComplianceRecordCountAggregateOutputType> | number
          }
        }
      }
      RiskAssessment: {
        payload: Prisma.$RiskAssessmentPayload<ExtArgs>
        fields: Prisma.RiskAssessmentFieldRefs
        operations: {
          findUnique: {
            args: Prisma.RiskAssessmentFindUniqueArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$RiskAssessmentPayload> | null
          }
          findUniqueOrThrow: {
            args: Prisma.RiskAssessmentFindUniqueOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$RiskAssessmentPayload>
          }
          findFirst: {
            args: Prisma.RiskAssessmentFindFirstArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$RiskAssessmentPayload> | null
          }
          findFirstOrThrow: {
            args: Prisma.RiskAssessmentFindFirstOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$RiskAssessmentPayload>
          }
          findMany: {
            args: Prisma.RiskAssessmentFindManyArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$RiskAssessmentPayload>[]
          }
          create: {
            args: Prisma.RiskAssessmentCreateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$RiskAssessmentPayload>
          }
          createMany: {
            args: Prisma.RiskAssessmentCreateManyArgs<ExtArgs>
            result: BatchPayload
          }
          createManyAndReturn: {
            args: Prisma.RiskAssessmentCreateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$RiskAssessmentPayload>[]
          }
          delete: {
            args: Prisma.RiskAssessmentDeleteArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$RiskAssessmentPayload>
          }
          update: {
            args: Prisma.RiskAssessmentUpdateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$RiskAssessmentPayload>
          }
          deleteMany: {
            args: Prisma.RiskAssessmentDeleteManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateMany: {
            args: Prisma.RiskAssessmentUpdateManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateManyAndReturn: {
            args: Prisma.RiskAssessmentUpdateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$RiskAssessmentPayload>[]
          }
          upsert: {
            args: Prisma.RiskAssessmentUpsertArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$RiskAssessmentPayload>
          }
          aggregate: {
            args: Prisma.RiskAssessmentAggregateArgs<ExtArgs>
            result: $Utils.Optional<AggregateRiskAssessment>
          }
          groupBy: {
            args: Prisma.RiskAssessmentGroupByArgs<ExtArgs>
            result: $Utils.Optional<RiskAssessmentGroupByOutputType>[]
          }
          count: {
            args: Prisma.RiskAssessmentCountArgs<ExtArgs>
            result: $Utils.Optional<RiskAssessmentCountAggregateOutputType> | number
          }
        }
      }
      AuditLog: {
        payload: Prisma.$AuditLogPayload<ExtArgs>
        fields: Prisma.AuditLogFieldRefs
        operations: {
          findUnique: {
            args: Prisma.AuditLogFindUniqueArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$AuditLogPayload> | null
          }
          findUniqueOrThrow: {
            args: Prisma.AuditLogFindUniqueOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$AuditLogPayload>
          }
          findFirst: {
            args: Prisma.AuditLogFindFirstArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$AuditLogPayload> | null
          }
          findFirstOrThrow: {
            args: Prisma.AuditLogFindFirstOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$AuditLogPayload>
          }
          findMany: {
            args: Prisma.AuditLogFindManyArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$AuditLogPayload>[]
          }
          create: {
            args: Prisma.AuditLogCreateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$AuditLogPayload>
          }
          createMany: {
            args: Prisma.AuditLogCreateManyArgs<ExtArgs>
            result: BatchPayload
          }
          createManyAndReturn: {
            args: Prisma.AuditLogCreateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$AuditLogPayload>[]
          }
          delete: {
            args: Prisma.AuditLogDeleteArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$AuditLogPayload>
          }
          update: {
            args: Prisma.AuditLogUpdateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$AuditLogPayload>
          }
          deleteMany: {
            args: Prisma.AuditLogDeleteManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateMany: {
            args: Prisma.AuditLogUpdateManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateManyAndReturn: {
            args: Prisma.AuditLogUpdateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$AuditLogPayload>[]
          }
          upsert: {
            args: Prisma.AuditLogUpsertArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$AuditLogPayload>
          }
          aggregate: {
            args: Prisma.AuditLogAggregateArgs<ExtArgs>
            result: $Utils.Optional<AggregateAuditLog>
          }
          groupBy: {
            args: Prisma.AuditLogGroupByArgs<ExtArgs>
            result: $Utils.Optional<AuditLogGroupByOutputType>[]
          }
          count: {
            args: Prisma.AuditLogCountArgs<ExtArgs>
            result: $Utils.Optional<AuditLogCountAggregateOutputType> | number
          }
        }
      }
    }
  } & {
    other: {
      payload: any
      operations: {
        $executeRaw: {
          args: [query: TemplateStringsArray | Prisma.Sql, ...values: any[]],
          result: any
        }
        $executeRawUnsafe: {
          args: [query: string, ...values: any[]],
          result: any
        }
        $queryRaw: {
          args: [query: TemplateStringsArray | Prisma.Sql, ...values: any[]],
          result: any
        }
        $queryRawUnsafe: {
          args: [query: string, ...values: any[]],
          result: any
        }
      }
    }
  }
  export const defineExtension: $Extensions.ExtendsHook<"define", Prisma.TypeMapCb, $Extensions.DefaultArgs>
  export type DefaultPrismaClient = PrismaClient
  export type ErrorFormat = 'pretty' | 'colorless' | 'minimal'
  export interface PrismaClientOptions {
    /**
     * Overwrites the datasource url from your schema.prisma file
     */
    datasources?: Datasources
    /**
     * Overwrites the datasource url from your schema.prisma file
     */
    datasourceUrl?: string
    /**
     * @default "colorless"
     */
    errorFormat?: ErrorFormat
    /**
     * @example
     * ```
     * // Defaults to stdout
     * log: ['query', 'info', 'warn', 'error']
     * 
     * // Emit as events
     * log: [
     *   { emit: 'stdout', level: 'query' },
     *   { emit: 'stdout', level: 'info' },
     *   { emit: 'stdout', level: 'warn' }
     *   { emit: 'stdout', level: 'error' }
     * ]
     * ```
     * Read more in our [docs](https://www.prisma.io/docs/reference/tools-and-interfaces/prisma-client/logging#the-log-option).
     */
    log?: (LogLevel | LogDefinition)[]
    /**
     * The default values for transactionOptions
     * maxWait ?= 2000
     * timeout ?= 5000
     */
    transactionOptions?: {
      maxWait?: number
      timeout?: number
      isolationLevel?: Prisma.TransactionIsolationLevel
    }
    /**
     * Global configuration for omitting model fields by default.
     * 
     * @example
     * ```
     * const prisma = new PrismaClient({
     *   omit: {
     *     user: {
     *       password: true
     *     }
     *   }
     * })
     * ```
     */
    omit?: Prisma.GlobalOmitConfig
  }
  export type GlobalOmitConfig = {
    user?: UserOmit
    simulation?: SimulationOmit
    biasDetectionResult?: BiasDetectionResultOmit
    fairnessAssessment?: FairnessAssessmentOmit
    explainabilityAnalysis?: ExplainabilityAnalysisOmit
    complianceRecord?: ComplianceRecordOmit
    riskAssessment?: RiskAssessmentOmit
    auditLog?: AuditLogOmit
  }

  /* Types for Logging */
  export type LogLevel = 'info' | 'query' | 'warn' | 'error'
  export type LogDefinition = {
    level: LogLevel
    emit: 'stdout' | 'event'
  }

  export type GetLogType<T extends LogLevel | LogDefinition> = T extends LogDefinition ? T['emit'] extends 'event' ? T['level'] : never : never
  export type GetEvents<T extends any> = T extends Array<LogLevel | LogDefinition> ?
    GetLogType<T[0]> | GetLogType<T[1]> | GetLogType<T[2]> | GetLogType<T[3]>
    : never

  export type QueryEvent = {
    timestamp: Date
    query: string
    params: string
    duration: number
    target: string
  }

  export type LogEvent = {
    timestamp: Date
    message: string
    target: string
  }
  /* End Types for Logging */


  export type PrismaAction =
    | 'findUnique'
    | 'findUniqueOrThrow'
    | 'findMany'
    | 'findFirst'
    | 'findFirstOrThrow'
    | 'create'
    | 'createMany'
    | 'createManyAndReturn'
    | 'update'
    | 'updateMany'
    | 'updateManyAndReturn'
    | 'upsert'
    | 'delete'
    | 'deleteMany'
    | 'executeRaw'
    | 'queryRaw'
    | 'aggregate'
    | 'count'
    | 'runCommandRaw'
    | 'findRaw'
    | 'groupBy'

  /**
   * These options are being passed into the middleware as "params"
   */
  export type MiddlewareParams = {
    model?: ModelName
    action: PrismaAction
    args: any
    dataPath: string[]
    runInTransaction: boolean
  }

  /**
   * The `T` type makes sure, that the `return proceed` is not forgotten in the middleware implementation
   */
  export type Middleware<T = any> = (
    params: MiddlewareParams,
    next: (params: MiddlewareParams) => $Utils.JsPromise<T>,
  ) => $Utils.JsPromise<T>

  // tested in getLogLevel.test.ts
  export function getLogLevel(log: Array<LogLevel | LogDefinition>): LogLevel | undefined;

  /**
   * `PrismaClient` proxy available in interactive transactions.
   */
  export type TransactionClient = Omit<Prisma.DefaultPrismaClient, runtime.ITXClientDenyList>

  export type Datasource = {
    url?: string
  }

  /**
   * Count Types
   */


  /**
   * Count Type UserCountOutputType
   */

  export type UserCountOutputType = {
    simulations: number
    auditLogs: number
  }

  export type UserCountOutputTypeSelect<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    simulations?: boolean | UserCountOutputTypeCountSimulationsArgs
    auditLogs?: boolean | UserCountOutputTypeCountAuditLogsArgs
  }

  // Custom InputTypes
  /**
   * UserCountOutputType without action
   */
  export type UserCountOutputTypeDefaultArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the UserCountOutputType
     */
    select?: UserCountOutputTypeSelect<ExtArgs> | null
  }

  /**
   * UserCountOutputType without action
   */
  export type UserCountOutputTypeCountSimulationsArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: SimulationWhereInput
  }

  /**
   * UserCountOutputType without action
   */
  export type UserCountOutputTypeCountAuditLogsArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: AuditLogWhereInput
  }


  /**
   * Count Type SimulationCountOutputType
   */

  export type SimulationCountOutputType = {
    BiasDetectionResult: number
    FairnessAssessment: number
    ExplainabilityAnalysis: number
    ComplianceRecord: number
    RiskAssessment: number
    auditLogs: number
  }

  export type SimulationCountOutputTypeSelect<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    BiasDetectionResult?: boolean | SimulationCountOutputTypeCountBiasDetectionResultArgs
    FairnessAssessment?: boolean | SimulationCountOutputTypeCountFairnessAssessmentArgs
    ExplainabilityAnalysis?: boolean | SimulationCountOutputTypeCountExplainabilityAnalysisArgs
    ComplianceRecord?: boolean | SimulationCountOutputTypeCountComplianceRecordArgs
    RiskAssessment?: boolean | SimulationCountOutputTypeCountRiskAssessmentArgs
    auditLogs?: boolean | SimulationCountOutputTypeCountAuditLogsArgs
  }

  // Custom InputTypes
  /**
   * SimulationCountOutputType without action
   */
  export type SimulationCountOutputTypeDefaultArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the SimulationCountOutputType
     */
    select?: SimulationCountOutputTypeSelect<ExtArgs> | null
  }

  /**
   * SimulationCountOutputType without action
   */
  export type SimulationCountOutputTypeCountBiasDetectionResultArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: BiasDetectionResultWhereInput
  }

  /**
   * SimulationCountOutputType without action
   */
  export type SimulationCountOutputTypeCountFairnessAssessmentArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: FairnessAssessmentWhereInput
  }

  /**
   * SimulationCountOutputType without action
   */
  export type SimulationCountOutputTypeCountExplainabilityAnalysisArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: ExplainabilityAnalysisWhereInput
  }

  /**
   * SimulationCountOutputType without action
   */
  export type SimulationCountOutputTypeCountComplianceRecordArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: ComplianceRecordWhereInput
  }

  /**
   * SimulationCountOutputType without action
   */
  export type SimulationCountOutputTypeCountRiskAssessmentArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: RiskAssessmentWhereInput
  }

  /**
   * SimulationCountOutputType without action
   */
  export type SimulationCountOutputTypeCountAuditLogsArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: AuditLogWhereInput
  }


  /**
   * Models
   */

  /**
   * Model User
   */

  export type AggregateUser = {
    _count: UserCountAggregateOutputType | null
    _avg: UserAvgAggregateOutputType | null
    _sum: UserSumAggregateOutputType | null
    _min: UserMinAggregateOutputType | null
    _max: UserMaxAggregateOutputType | null
  }

  export type UserAvgAggregateOutputType = {
    id: number | null
  }

  export type UserSumAggregateOutputType = {
    id: number | null
  }

  export type UserMinAggregateOutputType = {
    id: number | null
    createdAt: Date | null
    updatedAt: Date | null
    email: string | null
    passwordHash: string | null
    name: string | null
    role: string | null
  }

  export type UserMaxAggregateOutputType = {
    id: number | null
    createdAt: Date | null
    updatedAt: Date | null
    email: string | null
    passwordHash: string | null
    name: string | null
    role: string | null
  }

  export type UserCountAggregateOutputType = {
    id: number
    createdAt: number
    updatedAt: number
    email: number
    passwordHash: number
    name: number
    role: number
    _all: number
  }


  export type UserAvgAggregateInputType = {
    id?: true
  }

  export type UserSumAggregateInputType = {
    id?: true
  }

  export type UserMinAggregateInputType = {
    id?: true
    createdAt?: true
    updatedAt?: true
    email?: true
    passwordHash?: true
    name?: true
    role?: true
  }

  export type UserMaxAggregateInputType = {
    id?: true
    createdAt?: true
    updatedAt?: true
    email?: true
    passwordHash?: true
    name?: true
    role?: true
  }

  export type UserCountAggregateInputType = {
    id?: true
    createdAt?: true
    updatedAt?: true
    email?: true
    passwordHash?: true
    name?: true
    role?: true
    _all?: true
  }

  export type UserAggregateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which User to aggregate.
     */
    where?: UserWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of Users to fetch.
     */
    orderBy?: UserOrderByWithRelationInput | UserOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the start position
     */
    cursor?: UserWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` Users from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` Users.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Count returned Users
    **/
    _count?: true | UserCountAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to average
    **/
    _avg?: UserAvgAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to sum
    **/
    _sum?: UserSumAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the minimum value
    **/
    _min?: UserMinAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the maximum value
    **/
    _max?: UserMaxAggregateInputType
  }

  export type GetUserAggregateType<T extends UserAggregateArgs> = {
        [P in keyof T & keyof AggregateUser]: P extends '_count' | 'count'
      ? T[P] extends true
        ? number
        : GetScalarType<T[P], AggregateUser[P]>
      : GetScalarType<T[P], AggregateUser[P]>
  }




  export type UserGroupByArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: UserWhereInput
    orderBy?: UserOrderByWithAggregationInput | UserOrderByWithAggregationInput[]
    by: UserScalarFieldEnum[] | UserScalarFieldEnum
    having?: UserScalarWhereWithAggregatesInput
    take?: number
    skip?: number
    _count?: UserCountAggregateInputType | true
    _avg?: UserAvgAggregateInputType
    _sum?: UserSumAggregateInputType
    _min?: UserMinAggregateInputType
    _max?: UserMaxAggregateInputType
  }

  export type UserGroupByOutputType = {
    id: number
    createdAt: Date
    updatedAt: Date
    email: string
    passwordHash: string
    name: string
    role: string
    _count: UserCountAggregateOutputType | null
    _avg: UserAvgAggregateOutputType | null
    _sum: UserSumAggregateOutputType | null
    _min: UserMinAggregateOutputType | null
    _max: UserMaxAggregateOutputType | null
  }

  type GetUserGroupByPayload<T extends UserGroupByArgs> = Prisma.PrismaPromise<
    Array<
      PickEnumerable<UserGroupByOutputType, T['by']> &
        {
          [P in ((keyof T) & (keyof UserGroupByOutputType))]: P extends '_count'
            ? T[P] extends boolean
              ? number
              : GetScalarType<T[P], UserGroupByOutputType[P]>
            : GetScalarType<T[P], UserGroupByOutputType[P]>
        }
      >
    >


  export type UserSelect<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    email?: boolean
    passwordHash?: boolean
    name?: boolean
    role?: boolean
    simulations?: boolean | User$simulationsArgs<ExtArgs>
    auditLogs?: boolean | User$auditLogsArgs<ExtArgs>
    _count?: boolean | UserCountOutputTypeDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["user"]>

  export type UserSelectCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    email?: boolean
    passwordHash?: boolean
    name?: boolean
    role?: boolean
  }, ExtArgs["result"]["user"]>

  export type UserSelectUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    email?: boolean
    passwordHash?: boolean
    name?: boolean
    role?: boolean
  }, ExtArgs["result"]["user"]>

  export type UserSelectScalar = {
    id?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    email?: boolean
    passwordHash?: boolean
    name?: boolean
    role?: boolean
  }

  export type UserOmit<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetOmit<"id" | "createdAt" | "updatedAt" | "email" | "passwordHash" | "name" | "role", ExtArgs["result"]["user"]>
  export type UserInclude<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    simulations?: boolean | User$simulationsArgs<ExtArgs>
    auditLogs?: boolean | User$auditLogsArgs<ExtArgs>
    _count?: boolean | UserCountOutputTypeDefaultArgs<ExtArgs>
  }
  export type UserIncludeCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {}
  export type UserIncludeUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {}

  export type $UserPayload<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    name: "User"
    objects: {
      simulations: Prisma.$SimulationPayload<ExtArgs>[]
      auditLogs: Prisma.$AuditLogPayload<ExtArgs>[]
    }
    scalars: $Extensions.GetPayloadResult<{
      id: number
      createdAt: Date
      updatedAt: Date
      email: string
      passwordHash: string
      name: string
      role: string
    }, ExtArgs["result"]["user"]>
    composites: {}
  }

  type UserGetPayload<S extends boolean | null | undefined | UserDefaultArgs> = $Result.GetResult<Prisma.$UserPayload, S>

  type UserCountArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> =
    Omit<UserFindManyArgs, 'select' | 'include' | 'distinct' | 'omit'> & {
      select?: UserCountAggregateInputType | true
    }

  export interface UserDelegate<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> {
    [K: symbol]: { types: Prisma.TypeMap<ExtArgs>['model']['User'], meta: { name: 'User' } }
    /**
     * Find zero or one User that matches the filter.
     * @param {UserFindUniqueArgs} args - Arguments to find a User
     * @example
     * // Get one User
     * const user = await prisma.user.findUnique({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUnique<T extends UserFindUniqueArgs>(args: SelectSubset<T, UserFindUniqueArgs<ExtArgs>>): Prisma__UserClient<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "findUnique", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find one User that matches the filter or throw an error with `error.code='P2025'`
     * if no matches were found.
     * @param {UserFindUniqueOrThrowArgs} args - Arguments to find a User
     * @example
     * // Get one User
     * const user = await prisma.user.findUniqueOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUniqueOrThrow<T extends UserFindUniqueOrThrowArgs>(args: SelectSubset<T, UserFindUniqueOrThrowArgs<ExtArgs>>): Prisma__UserClient<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first User that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {UserFindFirstArgs} args - Arguments to find a User
     * @example
     * // Get one User
     * const user = await prisma.user.findFirst({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirst<T extends UserFindFirstArgs>(args?: SelectSubset<T, UserFindFirstArgs<ExtArgs>>): Prisma__UserClient<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "findFirst", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first User that matches the filter or
     * throw `PrismaKnownClientError` with `P2025` code if no matches were found.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {UserFindFirstOrThrowArgs} args - Arguments to find a User
     * @example
     * // Get one User
     * const user = await prisma.user.findFirstOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirstOrThrow<T extends UserFindFirstOrThrowArgs>(args?: SelectSubset<T, UserFindFirstOrThrowArgs<ExtArgs>>): Prisma__UserClient<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "findFirstOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find zero or more Users that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {UserFindManyArgs} args - Arguments to filter and select certain fields only.
     * @example
     * // Get all Users
     * const users = await prisma.user.findMany()
     * 
     * // Get first 10 Users
     * const users = await prisma.user.findMany({ take: 10 })
     * 
     * // Only select the `id`
     * const userWithIdOnly = await prisma.user.findMany({ select: { id: true } })
     * 
     */
    findMany<T extends UserFindManyArgs>(args?: SelectSubset<T, UserFindManyArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "findMany", GlobalOmitOptions>>

    /**
     * Create a User.
     * @param {UserCreateArgs} args - Arguments to create a User.
     * @example
     * // Create one User
     * const User = await prisma.user.create({
     *   data: {
     *     // ... data to create a User
     *   }
     * })
     * 
     */
    create<T extends UserCreateArgs>(args: SelectSubset<T, UserCreateArgs<ExtArgs>>): Prisma__UserClient<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "create", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Create many Users.
     * @param {UserCreateManyArgs} args - Arguments to create many Users.
     * @example
     * // Create many Users
     * const user = await prisma.user.createMany({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     *     
     */
    createMany<T extends UserCreateManyArgs>(args?: SelectSubset<T, UserCreateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Create many Users and returns the data saved in the database.
     * @param {UserCreateManyAndReturnArgs} args - Arguments to create many Users.
     * @example
     * // Create many Users
     * const user = await prisma.user.createManyAndReturn({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Create many Users and only return the `id`
     * const userWithIdOnly = await prisma.user.createManyAndReturn({
     *   select: { id: true },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    createManyAndReturn<T extends UserCreateManyAndReturnArgs>(args?: SelectSubset<T, UserCreateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "createManyAndReturn", GlobalOmitOptions>>

    /**
     * Delete a User.
     * @param {UserDeleteArgs} args - Arguments to delete one User.
     * @example
     * // Delete one User
     * const User = await prisma.user.delete({
     *   where: {
     *     // ... filter to delete one User
     *   }
     * })
     * 
     */
    delete<T extends UserDeleteArgs>(args: SelectSubset<T, UserDeleteArgs<ExtArgs>>): Prisma__UserClient<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "delete", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Update one User.
     * @param {UserUpdateArgs} args - Arguments to update one User.
     * @example
     * // Update one User
     * const user = await prisma.user.update({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    update<T extends UserUpdateArgs>(args: SelectSubset<T, UserUpdateArgs<ExtArgs>>): Prisma__UserClient<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "update", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Delete zero or more Users.
     * @param {UserDeleteManyArgs} args - Arguments to filter Users to delete.
     * @example
     * // Delete a few Users
     * const { count } = await prisma.user.deleteMany({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     * 
     */
    deleteMany<T extends UserDeleteManyArgs>(args?: SelectSubset<T, UserDeleteManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more Users.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {UserUpdateManyArgs} args - Arguments to update one or more rows.
     * @example
     * // Update many Users
     * const user = await prisma.user.updateMany({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    updateMany<T extends UserUpdateManyArgs>(args: SelectSubset<T, UserUpdateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more Users and returns the data updated in the database.
     * @param {UserUpdateManyAndReturnArgs} args - Arguments to update many Users.
     * @example
     * // Update many Users
     * const user = await prisma.user.updateManyAndReturn({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Update zero or more Users and only return the `id`
     * const userWithIdOnly = await prisma.user.updateManyAndReturn({
     *   select: { id: true },
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    updateManyAndReturn<T extends UserUpdateManyAndReturnArgs>(args: SelectSubset<T, UserUpdateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "updateManyAndReturn", GlobalOmitOptions>>

    /**
     * Create or update one User.
     * @param {UserUpsertArgs} args - Arguments to update or create a User.
     * @example
     * // Update or create a User
     * const user = await prisma.user.upsert({
     *   create: {
     *     // ... data to create a User
     *   },
     *   update: {
     *     // ... in case it already exists, update
     *   },
     *   where: {
     *     // ... the filter for the User we want to update
     *   }
     * })
     */
    upsert<T extends UserUpsertArgs>(args: SelectSubset<T, UserUpsertArgs<ExtArgs>>): Prisma__UserClient<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "upsert", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>


    /**
     * Count the number of Users.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {UserCountArgs} args - Arguments to filter Users to count.
     * @example
     * // Count the number of Users
     * const count = await prisma.user.count({
     *   where: {
     *     // ... the filter for the Users we want to count
     *   }
     * })
    **/
    count<T extends UserCountArgs>(
      args?: Subset<T, UserCountArgs>,
    ): Prisma.PrismaPromise<
      T extends $Utils.Record<'select', any>
        ? T['select'] extends true
          ? number
          : GetScalarType<T['select'], UserCountAggregateOutputType>
        : number
    >

    /**
     * Allows you to perform aggregations operations on a User.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {UserAggregateArgs} args - Select which aggregations you would like to apply and on what fields.
     * @example
     * // Ordered by age ascending
     * // Where email contains prisma.io
     * // Limited to the 10 users
     * const aggregations = await prisma.user.aggregate({
     *   _avg: {
     *     age: true,
     *   },
     *   where: {
     *     email: {
     *       contains: "prisma.io",
     *     },
     *   },
     *   orderBy: {
     *     age: "asc",
     *   },
     *   take: 10,
     * })
    **/
    aggregate<T extends UserAggregateArgs>(args: Subset<T, UserAggregateArgs>): Prisma.PrismaPromise<GetUserAggregateType<T>>

    /**
     * Group by User.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {UserGroupByArgs} args - Group by arguments.
     * @example
     * // Group by city, order by createdAt, get count
     * const result = await prisma.user.groupBy({
     *   by: ['city', 'createdAt'],
     *   orderBy: {
     *     createdAt: true
     *   },
     *   _count: {
     *     _all: true
     *   },
     * })
     * 
    **/
    groupBy<
      T extends UserGroupByArgs,
      HasSelectOrTake extends Or<
        Extends<'skip', Keys<T>>,
        Extends<'take', Keys<T>>
      >,
      OrderByArg extends True extends HasSelectOrTake
        ? { orderBy: UserGroupByArgs['orderBy'] }
        : { orderBy?: UserGroupByArgs['orderBy'] },
      OrderFields extends ExcludeUnderscoreKeys<Keys<MaybeTupleToUnion<T['orderBy']>>>,
      ByFields extends MaybeTupleToUnion<T['by']>,
      ByValid extends Has<ByFields, OrderFields>,
      HavingFields extends GetHavingFields<T['having']>,
      HavingValid extends Has<ByFields, HavingFields>,
      ByEmpty extends T['by'] extends never[] ? True : False,
      InputErrors extends ByEmpty extends True
      ? `Error: "by" must not be empty.`
      : HavingValid extends False
      ? {
          [P in HavingFields]: P extends ByFields
            ? never
            : P extends string
            ? `Error: Field "${P}" used in "having" needs to be provided in "by".`
            : [
                Error,
                'Field ',
                P,
                ` in "having" needs to be provided in "by"`,
              ]
        }[HavingFields]
      : 'take' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "take", you also need to provide "orderBy"'
      : 'skip' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "skip", you also need to provide "orderBy"'
      : ByValid extends True
      ? {}
      : {
          [P in OrderFields]: P extends ByFields
            ? never
            : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
        }[OrderFields]
    >(args: SubsetIntersection<T, UserGroupByArgs, OrderByArg> & InputErrors): {} extends InputErrors ? GetUserGroupByPayload<T> : Prisma.PrismaPromise<InputErrors>
  /**
   * Fields of the User model
   */
  readonly fields: UserFieldRefs;
  }

  /**
   * The delegate class that acts as a "Promise-like" for User.
   * Why is this prefixed with `Prisma__`?
   * Because we want to prevent naming conflicts as mentioned in
   * https://github.com/prisma/prisma-client-js/issues/707
   */
  export interface Prisma__UserClient<T, Null = never, ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> extends Prisma.PrismaPromise<T> {
    readonly [Symbol.toStringTag]: "PrismaPromise"
    simulations<T extends User$simulationsArgs<ExtArgs> = {}>(args?: Subset<T, User$simulationsArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$SimulationPayload<ExtArgs>, T, "findMany", GlobalOmitOptions> | Null>
    auditLogs<T extends User$auditLogsArgs<ExtArgs> = {}>(args?: Subset<T, User$auditLogsArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$AuditLogPayload<ExtArgs>, T, "findMany", GlobalOmitOptions> | Null>
    /**
     * Attaches callbacks for the resolution and/or rejection of the Promise.
     * @param onfulfilled The callback to execute when the Promise is resolved.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of which ever callback is executed.
     */
    then<TResult1 = T, TResult2 = never>(onfulfilled?: ((value: T) => TResult1 | PromiseLike<TResult1>) | undefined | null, onrejected?: ((reason: any) => TResult2 | PromiseLike<TResult2>) | undefined | null): $Utils.JsPromise<TResult1 | TResult2>
    /**
     * Attaches a callback for only the rejection of the Promise.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of the callback.
     */
    catch<TResult = never>(onrejected?: ((reason: any) => TResult | PromiseLike<TResult>) | undefined | null): $Utils.JsPromise<T | TResult>
    /**
     * Attaches a callback that is invoked when the Promise is settled (fulfilled or rejected). The
     * resolved value cannot be modified from the callback.
     * @param onfinally The callback to execute when the Promise is settled (fulfilled or rejected).
     * @returns A Promise for the completion of the callback.
     */
    finally(onfinally?: (() => void) | undefined | null): $Utils.JsPromise<T>
  }




  /**
   * Fields of the User model
   */
  interface UserFieldRefs {
    readonly id: FieldRef<"User", 'Int'>
    readonly createdAt: FieldRef<"User", 'DateTime'>
    readonly updatedAt: FieldRef<"User", 'DateTime'>
    readonly email: FieldRef<"User", 'String'>
    readonly passwordHash: FieldRef<"User", 'String'>
    readonly name: FieldRef<"User", 'String'>
    readonly role: FieldRef<"User", 'String'>
  }
    

  // Custom InputTypes
  /**
   * User findUnique
   */
  export type UserFindUniqueArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelect<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: UserInclude<ExtArgs> | null
    /**
     * Filter, which User to fetch.
     */
    where: UserWhereUniqueInput
  }

  /**
   * User findUniqueOrThrow
   */
  export type UserFindUniqueOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelect<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: UserInclude<ExtArgs> | null
    /**
     * Filter, which User to fetch.
     */
    where: UserWhereUniqueInput
  }

  /**
   * User findFirst
   */
  export type UserFindFirstArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelect<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: UserInclude<ExtArgs> | null
    /**
     * Filter, which User to fetch.
     */
    where?: UserWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of Users to fetch.
     */
    orderBy?: UserOrderByWithRelationInput | UserOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for Users.
     */
    cursor?: UserWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` Users from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` Users.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of Users.
     */
    distinct?: UserScalarFieldEnum | UserScalarFieldEnum[]
  }

  /**
   * User findFirstOrThrow
   */
  export type UserFindFirstOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelect<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: UserInclude<ExtArgs> | null
    /**
     * Filter, which User to fetch.
     */
    where?: UserWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of Users to fetch.
     */
    orderBy?: UserOrderByWithRelationInput | UserOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for Users.
     */
    cursor?: UserWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` Users from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` Users.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of Users.
     */
    distinct?: UserScalarFieldEnum | UserScalarFieldEnum[]
  }

  /**
   * User findMany
   */
  export type UserFindManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelect<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: UserInclude<ExtArgs> | null
    /**
     * Filter, which Users to fetch.
     */
    where?: UserWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of Users to fetch.
     */
    orderBy?: UserOrderByWithRelationInput | UserOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for listing Users.
     */
    cursor?: UserWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` Users from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` Users.
     */
    skip?: number
    distinct?: UserScalarFieldEnum | UserScalarFieldEnum[]
  }

  /**
   * User create
   */
  export type UserCreateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelect<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: UserInclude<ExtArgs> | null
    /**
     * The data needed to create a User.
     */
    data: XOR<UserCreateInput, UserUncheckedCreateInput>
  }

  /**
   * User createMany
   */
  export type UserCreateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to create many Users.
     */
    data: UserCreateManyInput | UserCreateManyInput[]
    skipDuplicates?: boolean
  }

  /**
   * User createManyAndReturn
   */
  export type UserCreateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelectCreateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * The data used to create many Users.
     */
    data: UserCreateManyInput | UserCreateManyInput[]
    skipDuplicates?: boolean
  }

  /**
   * User update
   */
  export type UserUpdateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelect<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: UserInclude<ExtArgs> | null
    /**
     * The data needed to update a User.
     */
    data: XOR<UserUpdateInput, UserUncheckedUpdateInput>
    /**
     * Choose, which User to update.
     */
    where: UserWhereUniqueInput
  }

  /**
   * User updateMany
   */
  export type UserUpdateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to update Users.
     */
    data: XOR<UserUpdateManyMutationInput, UserUncheckedUpdateManyInput>
    /**
     * Filter which Users to update
     */
    where?: UserWhereInput
    /**
     * Limit how many Users to update.
     */
    limit?: number
  }

  /**
   * User updateManyAndReturn
   */
  export type UserUpdateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelectUpdateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * The data used to update Users.
     */
    data: XOR<UserUpdateManyMutationInput, UserUncheckedUpdateManyInput>
    /**
     * Filter which Users to update
     */
    where?: UserWhereInput
    /**
     * Limit how many Users to update.
     */
    limit?: number
  }

  /**
   * User upsert
   */
  export type UserUpsertArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelect<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: UserInclude<ExtArgs> | null
    /**
     * The filter to search for the User to update in case it exists.
     */
    where: UserWhereUniqueInput
    /**
     * In case the User found by the `where` argument doesn't exist, create a new User with this data.
     */
    create: XOR<UserCreateInput, UserUncheckedCreateInput>
    /**
     * In case the User was found with the provided `where` argument, update it with this data.
     */
    update: XOR<UserUpdateInput, UserUncheckedUpdateInput>
  }

  /**
   * User delete
   */
  export type UserDeleteArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelect<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: UserInclude<ExtArgs> | null
    /**
     * Filter which User to delete.
     */
    where: UserWhereUniqueInput
  }

  /**
   * User deleteMany
   */
  export type UserDeleteManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which Users to delete
     */
    where?: UserWhereInput
    /**
     * Limit how many Users to delete.
     */
    limit?: number
  }

  /**
   * User.simulations
   */
  export type User$simulationsArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Simulation
     */
    select?: SimulationSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Simulation
     */
    omit?: SimulationOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: SimulationInclude<ExtArgs> | null
    where?: SimulationWhereInput
    orderBy?: SimulationOrderByWithRelationInput | SimulationOrderByWithRelationInput[]
    cursor?: SimulationWhereUniqueInput
    take?: number
    skip?: number
    distinct?: SimulationScalarFieldEnum | SimulationScalarFieldEnum[]
  }

  /**
   * User.auditLogs
   */
  export type User$auditLogsArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the AuditLog
     */
    select?: AuditLogSelect<ExtArgs> | null
    /**
     * Omit specific fields from the AuditLog
     */
    omit?: AuditLogOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: AuditLogInclude<ExtArgs> | null
    where?: AuditLogWhereInput
    orderBy?: AuditLogOrderByWithRelationInput | AuditLogOrderByWithRelationInput[]
    cursor?: AuditLogWhereUniqueInput
    take?: number
    skip?: number
    distinct?: AuditLogScalarFieldEnum | AuditLogScalarFieldEnum[]
  }

  /**
   * User without action
   */
  export type UserDefaultArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelect<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: UserInclude<ExtArgs> | null
  }


  /**
   * Model Simulation
   */

  export type AggregateSimulation = {
    _count: SimulationCountAggregateOutputType | null
    _avg: SimulationAvgAggregateOutputType | null
    _sum: SimulationSumAggregateOutputType | null
    _min: SimulationMinAggregateOutputType | null
    _max: SimulationMaxAggregateOutputType | null
  }

  export type SimulationAvgAggregateOutputType = {
    id: number | null
    userId: number | null
  }

  export type SimulationSumAggregateOutputType = {
    id: number | null
    userId: number | null
  }

  export type SimulationMinAggregateOutputType = {
    id: number | null
    createdAt: Date | null
    updatedAt: Date | null
    name: string | null
    description: string | null
    status: $Enums.SimulationStatus | null
    userId: number | null
    modelType: string | null
    version: string | null
  }

  export type SimulationMaxAggregateOutputType = {
    id: number | null
    createdAt: Date | null
    updatedAt: Date | null
    name: string | null
    description: string | null
    status: $Enums.SimulationStatus | null
    userId: number | null
    modelType: string | null
    version: string | null
  }

  export type SimulationCountAggregateOutputType = {
    id: number
    createdAt: number
    updatedAt: number
    name: number
    description: number
    status: number
    userId: number
    config: number
    modelType: number
    version: number
    tags: number
    _all: number
  }


  export type SimulationAvgAggregateInputType = {
    id?: true
    userId?: true
  }

  export type SimulationSumAggregateInputType = {
    id?: true
    userId?: true
  }

  export type SimulationMinAggregateInputType = {
    id?: true
    createdAt?: true
    updatedAt?: true
    name?: true
    description?: true
    status?: true
    userId?: true
    modelType?: true
    version?: true
  }

  export type SimulationMaxAggregateInputType = {
    id?: true
    createdAt?: true
    updatedAt?: true
    name?: true
    description?: true
    status?: true
    userId?: true
    modelType?: true
    version?: true
  }

  export type SimulationCountAggregateInputType = {
    id?: true
    createdAt?: true
    updatedAt?: true
    name?: true
    description?: true
    status?: true
    userId?: true
    config?: true
    modelType?: true
    version?: true
    tags?: true
    _all?: true
  }

  export type SimulationAggregateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which Simulation to aggregate.
     */
    where?: SimulationWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of Simulations to fetch.
     */
    orderBy?: SimulationOrderByWithRelationInput | SimulationOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the start position
     */
    cursor?: SimulationWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` Simulations from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` Simulations.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Count returned Simulations
    **/
    _count?: true | SimulationCountAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to average
    **/
    _avg?: SimulationAvgAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to sum
    **/
    _sum?: SimulationSumAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the minimum value
    **/
    _min?: SimulationMinAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the maximum value
    **/
    _max?: SimulationMaxAggregateInputType
  }

  export type GetSimulationAggregateType<T extends SimulationAggregateArgs> = {
        [P in keyof T & keyof AggregateSimulation]: P extends '_count' | 'count'
      ? T[P] extends true
        ? number
        : GetScalarType<T[P], AggregateSimulation[P]>
      : GetScalarType<T[P], AggregateSimulation[P]>
  }




  export type SimulationGroupByArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: SimulationWhereInput
    orderBy?: SimulationOrderByWithAggregationInput | SimulationOrderByWithAggregationInput[]
    by: SimulationScalarFieldEnum[] | SimulationScalarFieldEnum
    having?: SimulationScalarWhereWithAggregatesInput
    take?: number
    skip?: number
    _count?: SimulationCountAggregateInputType | true
    _avg?: SimulationAvgAggregateInputType
    _sum?: SimulationSumAggregateInputType
    _min?: SimulationMinAggregateInputType
    _max?: SimulationMaxAggregateInputType
  }

  export type SimulationGroupByOutputType = {
    id: number
    createdAt: Date
    updatedAt: Date
    name: string
    description: string | null
    status: $Enums.SimulationStatus
    userId: number
    config: JsonValue
    modelType: string
    version: string
    tags: string[]
    _count: SimulationCountAggregateOutputType | null
    _avg: SimulationAvgAggregateOutputType | null
    _sum: SimulationSumAggregateOutputType | null
    _min: SimulationMinAggregateOutputType | null
    _max: SimulationMaxAggregateOutputType | null
  }

  type GetSimulationGroupByPayload<T extends SimulationGroupByArgs> = Prisma.PrismaPromise<
    Array<
      PickEnumerable<SimulationGroupByOutputType, T['by']> &
        {
          [P in ((keyof T) & (keyof SimulationGroupByOutputType))]: P extends '_count'
            ? T[P] extends boolean
              ? number
              : GetScalarType<T[P], SimulationGroupByOutputType[P]>
            : GetScalarType<T[P], SimulationGroupByOutputType[P]>
        }
      >
    >


  export type SimulationSelect<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    name?: boolean
    description?: boolean
    status?: boolean
    userId?: boolean
    config?: boolean
    modelType?: boolean
    version?: boolean
    tags?: boolean
    user?: boolean | UserDefaultArgs<ExtArgs>
    BiasDetectionResult?: boolean | Simulation$BiasDetectionResultArgs<ExtArgs>
    FairnessAssessment?: boolean | Simulation$FairnessAssessmentArgs<ExtArgs>
    ExplainabilityAnalysis?: boolean | Simulation$ExplainabilityAnalysisArgs<ExtArgs>
    ComplianceRecord?: boolean | Simulation$ComplianceRecordArgs<ExtArgs>
    RiskAssessment?: boolean | Simulation$RiskAssessmentArgs<ExtArgs>
    auditLogs?: boolean | Simulation$auditLogsArgs<ExtArgs>
    _count?: boolean | SimulationCountOutputTypeDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["simulation"]>

  export type SimulationSelectCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    name?: boolean
    description?: boolean
    status?: boolean
    userId?: boolean
    config?: boolean
    modelType?: boolean
    version?: boolean
    tags?: boolean
    user?: boolean | UserDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["simulation"]>

  export type SimulationSelectUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    name?: boolean
    description?: boolean
    status?: boolean
    userId?: boolean
    config?: boolean
    modelType?: boolean
    version?: boolean
    tags?: boolean
    user?: boolean | UserDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["simulation"]>

  export type SimulationSelectScalar = {
    id?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    name?: boolean
    description?: boolean
    status?: boolean
    userId?: boolean
    config?: boolean
    modelType?: boolean
    version?: boolean
    tags?: boolean
  }

  export type SimulationOmit<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetOmit<"id" | "createdAt" | "updatedAt" | "name" | "description" | "status" | "userId" | "config" | "modelType" | "version" | "tags", ExtArgs["result"]["simulation"]>
  export type SimulationInclude<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    user?: boolean | UserDefaultArgs<ExtArgs>
    BiasDetectionResult?: boolean | Simulation$BiasDetectionResultArgs<ExtArgs>
    FairnessAssessment?: boolean | Simulation$FairnessAssessmentArgs<ExtArgs>
    ExplainabilityAnalysis?: boolean | Simulation$ExplainabilityAnalysisArgs<ExtArgs>
    ComplianceRecord?: boolean | Simulation$ComplianceRecordArgs<ExtArgs>
    RiskAssessment?: boolean | Simulation$RiskAssessmentArgs<ExtArgs>
    auditLogs?: boolean | Simulation$auditLogsArgs<ExtArgs>
    _count?: boolean | SimulationCountOutputTypeDefaultArgs<ExtArgs>
  }
  export type SimulationIncludeCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    user?: boolean | UserDefaultArgs<ExtArgs>
  }
  export type SimulationIncludeUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    user?: boolean | UserDefaultArgs<ExtArgs>
  }

  export type $SimulationPayload<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    name: "Simulation"
    objects: {
      user: Prisma.$UserPayload<ExtArgs>
      BiasDetectionResult: Prisma.$BiasDetectionResultPayload<ExtArgs>[]
      FairnessAssessment: Prisma.$FairnessAssessmentPayload<ExtArgs>[]
      ExplainabilityAnalysis: Prisma.$ExplainabilityAnalysisPayload<ExtArgs>[]
      ComplianceRecord: Prisma.$ComplianceRecordPayload<ExtArgs>[]
      RiskAssessment: Prisma.$RiskAssessmentPayload<ExtArgs>[]
      auditLogs: Prisma.$AuditLogPayload<ExtArgs>[]
    }
    scalars: $Extensions.GetPayloadResult<{
      id: number
      createdAt: Date
      updatedAt: Date
      name: string
      description: string | null
      status: $Enums.SimulationStatus
      userId: number
      config: Prisma.JsonValue
      modelType: string
      version: string
      tags: string[]
    }, ExtArgs["result"]["simulation"]>
    composites: {}
  }

  type SimulationGetPayload<S extends boolean | null | undefined | SimulationDefaultArgs> = $Result.GetResult<Prisma.$SimulationPayload, S>

  type SimulationCountArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> =
    Omit<SimulationFindManyArgs, 'select' | 'include' | 'distinct' | 'omit'> & {
      select?: SimulationCountAggregateInputType | true
    }

  export interface SimulationDelegate<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> {
    [K: symbol]: { types: Prisma.TypeMap<ExtArgs>['model']['Simulation'], meta: { name: 'Simulation' } }
    /**
     * Find zero or one Simulation that matches the filter.
     * @param {SimulationFindUniqueArgs} args - Arguments to find a Simulation
     * @example
     * // Get one Simulation
     * const simulation = await prisma.simulation.findUnique({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUnique<T extends SimulationFindUniqueArgs>(args: SelectSubset<T, SimulationFindUniqueArgs<ExtArgs>>): Prisma__SimulationClient<$Result.GetResult<Prisma.$SimulationPayload<ExtArgs>, T, "findUnique", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find one Simulation that matches the filter or throw an error with `error.code='P2025'`
     * if no matches were found.
     * @param {SimulationFindUniqueOrThrowArgs} args - Arguments to find a Simulation
     * @example
     * // Get one Simulation
     * const simulation = await prisma.simulation.findUniqueOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUniqueOrThrow<T extends SimulationFindUniqueOrThrowArgs>(args: SelectSubset<T, SimulationFindUniqueOrThrowArgs<ExtArgs>>): Prisma__SimulationClient<$Result.GetResult<Prisma.$SimulationPayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first Simulation that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {SimulationFindFirstArgs} args - Arguments to find a Simulation
     * @example
     * // Get one Simulation
     * const simulation = await prisma.simulation.findFirst({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirst<T extends SimulationFindFirstArgs>(args?: SelectSubset<T, SimulationFindFirstArgs<ExtArgs>>): Prisma__SimulationClient<$Result.GetResult<Prisma.$SimulationPayload<ExtArgs>, T, "findFirst", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first Simulation that matches the filter or
     * throw `PrismaKnownClientError` with `P2025` code if no matches were found.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {SimulationFindFirstOrThrowArgs} args - Arguments to find a Simulation
     * @example
     * // Get one Simulation
     * const simulation = await prisma.simulation.findFirstOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirstOrThrow<T extends SimulationFindFirstOrThrowArgs>(args?: SelectSubset<T, SimulationFindFirstOrThrowArgs<ExtArgs>>): Prisma__SimulationClient<$Result.GetResult<Prisma.$SimulationPayload<ExtArgs>, T, "findFirstOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find zero or more Simulations that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {SimulationFindManyArgs} args - Arguments to filter and select certain fields only.
     * @example
     * // Get all Simulations
     * const simulations = await prisma.simulation.findMany()
     * 
     * // Get first 10 Simulations
     * const simulations = await prisma.simulation.findMany({ take: 10 })
     * 
     * // Only select the `id`
     * const simulationWithIdOnly = await prisma.simulation.findMany({ select: { id: true } })
     * 
     */
    findMany<T extends SimulationFindManyArgs>(args?: SelectSubset<T, SimulationFindManyArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$SimulationPayload<ExtArgs>, T, "findMany", GlobalOmitOptions>>

    /**
     * Create a Simulation.
     * @param {SimulationCreateArgs} args - Arguments to create a Simulation.
     * @example
     * // Create one Simulation
     * const Simulation = await prisma.simulation.create({
     *   data: {
     *     // ... data to create a Simulation
     *   }
     * })
     * 
     */
    create<T extends SimulationCreateArgs>(args: SelectSubset<T, SimulationCreateArgs<ExtArgs>>): Prisma__SimulationClient<$Result.GetResult<Prisma.$SimulationPayload<ExtArgs>, T, "create", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Create many Simulations.
     * @param {SimulationCreateManyArgs} args - Arguments to create many Simulations.
     * @example
     * // Create many Simulations
     * const simulation = await prisma.simulation.createMany({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     *     
     */
    createMany<T extends SimulationCreateManyArgs>(args?: SelectSubset<T, SimulationCreateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Create many Simulations and returns the data saved in the database.
     * @param {SimulationCreateManyAndReturnArgs} args - Arguments to create many Simulations.
     * @example
     * // Create many Simulations
     * const simulation = await prisma.simulation.createManyAndReturn({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Create many Simulations and only return the `id`
     * const simulationWithIdOnly = await prisma.simulation.createManyAndReturn({
     *   select: { id: true },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    createManyAndReturn<T extends SimulationCreateManyAndReturnArgs>(args?: SelectSubset<T, SimulationCreateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$SimulationPayload<ExtArgs>, T, "createManyAndReturn", GlobalOmitOptions>>

    /**
     * Delete a Simulation.
     * @param {SimulationDeleteArgs} args - Arguments to delete one Simulation.
     * @example
     * // Delete one Simulation
     * const Simulation = await prisma.simulation.delete({
     *   where: {
     *     // ... filter to delete one Simulation
     *   }
     * })
     * 
     */
    delete<T extends SimulationDeleteArgs>(args: SelectSubset<T, SimulationDeleteArgs<ExtArgs>>): Prisma__SimulationClient<$Result.GetResult<Prisma.$SimulationPayload<ExtArgs>, T, "delete", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Update one Simulation.
     * @param {SimulationUpdateArgs} args - Arguments to update one Simulation.
     * @example
     * // Update one Simulation
     * const simulation = await prisma.simulation.update({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    update<T extends SimulationUpdateArgs>(args: SelectSubset<T, SimulationUpdateArgs<ExtArgs>>): Prisma__SimulationClient<$Result.GetResult<Prisma.$SimulationPayload<ExtArgs>, T, "update", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Delete zero or more Simulations.
     * @param {SimulationDeleteManyArgs} args - Arguments to filter Simulations to delete.
     * @example
     * // Delete a few Simulations
     * const { count } = await prisma.simulation.deleteMany({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     * 
     */
    deleteMany<T extends SimulationDeleteManyArgs>(args?: SelectSubset<T, SimulationDeleteManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more Simulations.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {SimulationUpdateManyArgs} args - Arguments to update one or more rows.
     * @example
     * // Update many Simulations
     * const simulation = await prisma.simulation.updateMany({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    updateMany<T extends SimulationUpdateManyArgs>(args: SelectSubset<T, SimulationUpdateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more Simulations and returns the data updated in the database.
     * @param {SimulationUpdateManyAndReturnArgs} args - Arguments to update many Simulations.
     * @example
     * // Update many Simulations
     * const simulation = await prisma.simulation.updateManyAndReturn({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Update zero or more Simulations and only return the `id`
     * const simulationWithIdOnly = await prisma.simulation.updateManyAndReturn({
     *   select: { id: true },
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    updateManyAndReturn<T extends SimulationUpdateManyAndReturnArgs>(args: SelectSubset<T, SimulationUpdateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$SimulationPayload<ExtArgs>, T, "updateManyAndReturn", GlobalOmitOptions>>

    /**
     * Create or update one Simulation.
     * @param {SimulationUpsertArgs} args - Arguments to update or create a Simulation.
     * @example
     * // Update or create a Simulation
     * const simulation = await prisma.simulation.upsert({
     *   create: {
     *     // ... data to create a Simulation
     *   },
     *   update: {
     *     // ... in case it already exists, update
     *   },
     *   where: {
     *     // ... the filter for the Simulation we want to update
     *   }
     * })
     */
    upsert<T extends SimulationUpsertArgs>(args: SelectSubset<T, SimulationUpsertArgs<ExtArgs>>): Prisma__SimulationClient<$Result.GetResult<Prisma.$SimulationPayload<ExtArgs>, T, "upsert", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>


    /**
     * Count the number of Simulations.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {SimulationCountArgs} args - Arguments to filter Simulations to count.
     * @example
     * // Count the number of Simulations
     * const count = await prisma.simulation.count({
     *   where: {
     *     // ... the filter for the Simulations we want to count
     *   }
     * })
    **/
    count<T extends SimulationCountArgs>(
      args?: Subset<T, SimulationCountArgs>,
    ): Prisma.PrismaPromise<
      T extends $Utils.Record<'select', any>
        ? T['select'] extends true
          ? number
          : GetScalarType<T['select'], SimulationCountAggregateOutputType>
        : number
    >

    /**
     * Allows you to perform aggregations operations on a Simulation.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {SimulationAggregateArgs} args - Select which aggregations you would like to apply and on what fields.
     * @example
     * // Ordered by age ascending
     * // Where email contains prisma.io
     * // Limited to the 10 users
     * const aggregations = await prisma.user.aggregate({
     *   _avg: {
     *     age: true,
     *   },
     *   where: {
     *     email: {
     *       contains: "prisma.io",
     *     },
     *   },
     *   orderBy: {
     *     age: "asc",
     *   },
     *   take: 10,
     * })
    **/
    aggregate<T extends SimulationAggregateArgs>(args: Subset<T, SimulationAggregateArgs>): Prisma.PrismaPromise<GetSimulationAggregateType<T>>

    /**
     * Group by Simulation.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {SimulationGroupByArgs} args - Group by arguments.
     * @example
     * // Group by city, order by createdAt, get count
     * const result = await prisma.user.groupBy({
     *   by: ['city', 'createdAt'],
     *   orderBy: {
     *     createdAt: true
     *   },
     *   _count: {
     *     _all: true
     *   },
     * })
     * 
    **/
    groupBy<
      T extends SimulationGroupByArgs,
      HasSelectOrTake extends Or<
        Extends<'skip', Keys<T>>,
        Extends<'take', Keys<T>>
      >,
      OrderByArg extends True extends HasSelectOrTake
        ? { orderBy: SimulationGroupByArgs['orderBy'] }
        : { orderBy?: SimulationGroupByArgs['orderBy'] },
      OrderFields extends ExcludeUnderscoreKeys<Keys<MaybeTupleToUnion<T['orderBy']>>>,
      ByFields extends MaybeTupleToUnion<T['by']>,
      ByValid extends Has<ByFields, OrderFields>,
      HavingFields extends GetHavingFields<T['having']>,
      HavingValid extends Has<ByFields, HavingFields>,
      ByEmpty extends T['by'] extends never[] ? True : False,
      InputErrors extends ByEmpty extends True
      ? `Error: "by" must not be empty.`
      : HavingValid extends False
      ? {
          [P in HavingFields]: P extends ByFields
            ? never
            : P extends string
            ? `Error: Field "${P}" used in "having" needs to be provided in "by".`
            : [
                Error,
                'Field ',
                P,
                ` in "having" needs to be provided in "by"`,
              ]
        }[HavingFields]
      : 'take' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "take", you also need to provide "orderBy"'
      : 'skip' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "skip", you also need to provide "orderBy"'
      : ByValid extends True
      ? {}
      : {
          [P in OrderFields]: P extends ByFields
            ? never
            : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
        }[OrderFields]
    >(args: SubsetIntersection<T, SimulationGroupByArgs, OrderByArg> & InputErrors): {} extends InputErrors ? GetSimulationGroupByPayload<T> : Prisma.PrismaPromise<InputErrors>
  /**
   * Fields of the Simulation model
   */
  readonly fields: SimulationFieldRefs;
  }

  /**
   * The delegate class that acts as a "Promise-like" for Simulation.
   * Why is this prefixed with `Prisma__`?
   * Because we want to prevent naming conflicts as mentioned in
   * https://github.com/prisma/prisma-client-js/issues/707
   */
  export interface Prisma__SimulationClient<T, Null = never, ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> extends Prisma.PrismaPromise<T> {
    readonly [Symbol.toStringTag]: "PrismaPromise"
    user<T extends UserDefaultArgs<ExtArgs> = {}>(args?: Subset<T, UserDefaultArgs<ExtArgs>>): Prisma__UserClient<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions> | Null, Null, ExtArgs, GlobalOmitOptions>
    BiasDetectionResult<T extends Simulation$BiasDetectionResultArgs<ExtArgs> = {}>(args?: Subset<T, Simulation$BiasDetectionResultArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$BiasDetectionResultPayload<ExtArgs>, T, "findMany", GlobalOmitOptions> | Null>
    FairnessAssessment<T extends Simulation$FairnessAssessmentArgs<ExtArgs> = {}>(args?: Subset<T, Simulation$FairnessAssessmentArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$FairnessAssessmentPayload<ExtArgs>, T, "findMany", GlobalOmitOptions> | Null>
    ExplainabilityAnalysis<T extends Simulation$ExplainabilityAnalysisArgs<ExtArgs> = {}>(args?: Subset<T, Simulation$ExplainabilityAnalysisArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$ExplainabilityAnalysisPayload<ExtArgs>, T, "findMany", GlobalOmitOptions> | Null>
    ComplianceRecord<T extends Simulation$ComplianceRecordArgs<ExtArgs> = {}>(args?: Subset<T, Simulation$ComplianceRecordArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$ComplianceRecordPayload<ExtArgs>, T, "findMany", GlobalOmitOptions> | Null>
    RiskAssessment<T extends Simulation$RiskAssessmentArgs<ExtArgs> = {}>(args?: Subset<T, Simulation$RiskAssessmentArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$RiskAssessmentPayload<ExtArgs>, T, "findMany", GlobalOmitOptions> | Null>
    auditLogs<T extends Simulation$auditLogsArgs<ExtArgs> = {}>(args?: Subset<T, Simulation$auditLogsArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$AuditLogPayload<ExtArgs>, T, "findMany", GlobalOmitOptions> | Null>
    /**
     * Attaches callbacks for the resolution and/or rejection of the Promise.
     * @param onfulfilled The callback to execute when the Promise is resolved.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of which ever callback is executed.
     */
    then<TResult1 = T, TResult2 = never>(onfulfilled?: ((value: T) => TResult1 | PromiseLike<TResult1>) | undefined | null, onrejected?: ((reason: any) => TResult2 | PromiseLike<TResult2>) | undefined | null): $Utils.JsPromise<TResult1 | TResult2>
    /**
     * Attaches a callback for only the rejection of the Promise.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of the callback.
     */
    catch<TResult = never>(onrejected?: ((reason: any) => TResult | PromiseLike<TResult>) | undefined | null): $Utils.JsPromise<T | TResult>
    /**
     * Attaches a callback that is invoked when the Promise is settled (fulfilled or rejected). The
     * resolved value cannot be modified from the callback.
     * @param onfinally The callback to execute when the Promise is settled (fulfilled or rejected).
     * @returns A Promise for the completion of the callback.
     */
    finally(onfinally?: (() => void) | undefined | null): $Utils.JsPromise<T>
  }




  /**
   * Fields of the Simulation model
   */
  interface SimulationFieldRefs {
    readonly id: FieldRef<"Simulation", 'Int'>
    readonly createdAt: FieldRef<"Simulation", 'DateTime'>
    readonly updatedAt: FieldRef<"Simulation", 'DateTime'>
    readonly name: FieldRef<"Simulation", 'String'>
    readonly description: FieldRef<"Simulation", 'String'>
    readonly status: FieldRef<"Simulation", 'SimulationStatus'>
    readonly userId: FieldRef<"Simulation", 'Int'>
    readonly config: FieldRef<"Simulation", 'Json'>
    readonly modelType: FieldRef<"Simulation", 'String'>
    readonly version: FieldRef<"Simulation", 'String'>
    readonly tags: FieldRef<"Simulation", 'String[]'>
  }
    

  // Custom InputTypes
  /**
   * Simulation findUnique
   */
  export type SimulationFindUniqueArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Simulation
     */
    select?: SimulationSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Simulation
     */
    omit?: SimulationOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: SimulationInclude<ExtArgs> | null
    /**
     * Filter, which Simulation to fetch.
     */
    where: SimulationWhereUniqueInput
  }

  /**
   * Simulation findUniqueOrThrow
   */
  export type SimulationFindUniqueOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Simulation
     */
    select?: SimulationSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Simulation
     */
    omit?: SimulationOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: SimulationInclude<ExtArgs> | null
    /**
     * Filter, which Simulation to fetch.
     */
    where: SimulationWhereUniqueInput
  }

  /**
   * Simulation findFirst
   */
  export type SimulationFindFirstArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Simulation
     */
    select?: SimulationSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Simulation
     */
    omit?: SimulationOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: SimulationInclude<ExtArgs> | null
    /**
     * Filter, which Simulation to fetch.
     */
    where?: SimulationWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of Simulations to fetch.
     */
    orderBy?: SimulationOrderByWithRelationInput | SimulationOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for Simulations.
     */
    cursor?: SimulationWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` Simulations from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` Simulations.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of Simulations.
     */
    distinct?: SimulationScalarFieldEnum | SimulationScalarFieldEnum[]
  }

  /**
   * Simulation findFirstOrThrow
   */
  export type SimulationFindFirstOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Simulation
     */
    select?: SimulationSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Simulation
     */
    omit?: SimulationOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: SimulationInclude<ExtArgs> | null
    /**
     * Filter, which Simulation to fetch.
     */
    where?: SimulationWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of Simulations to fetch.
     */
    orderBy?: SimulationOrderByWithRelationInput | SimulationOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for Simulations.
     */
    cursor?: SimulationWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` Simulations from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` Simulations.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of Simulations.
     */
    distinct?: SimulationScalarFieldEnum | SimulationScalarFieldEnum[]
  }

  /**
   * Simulation findMany
   */
  export type SimulationFindManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Simulation
     */
    select?: SimulationSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Simulation
     */
    omit?: SimulationOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: SimulationInclude<ExtArgs> | null
    /**
     * Filter, which Simulations to fetch.
     */
    where?: SimulationWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of Simulations to fetch.
     */
    orderBy?: SimulationOrderByWithRelationInput | SimulationOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for listing Simulations.
     */
    cursor?: SimulationWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` Simulations from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` Simulations.
     */
    skip?: number
    distinct?: SimulationScalarFieldEnum | SimulationScalarFieldEnum[]
  }

  /**
   * Simulation create
   */
  export type SimulationCreateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Simulation
     */
    select?: SimulationSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Simulation
     */
    omit?: SimulationOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: SimulationInclude<ExtArgs> | null
    /**
     * The data needed to create a Simulation.
     */
    data: XOR<SimulationCreateInput, SimulationUncheckedCreateInput>
  }

  /**
   * Simulation createMany
   */
  export type SimulationCreateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to create many Simulations.
     */
    data: SimulationCreateManyInput | SimulationCreateManyInput[]
    skipDuplicates?: boolean
  }

  /**
   * Simulation createManyAndReturn
   */
  export type SimulationCreateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Simulation
     */
    select?: SimulationSelectCreateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the Simulation
     */
    omit?: SimulationOmit<ExtArgs> | null
    /**
     * The data used to create many Simulations.
     */
    data: SimulationCreateManyInput | SimulationCreateManyInput[]
    skipDuplicates?: boolean
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: SimulationIncludeCreateManyAndReturn<ExtArgs> | null
  }

  /**
   * Simulation update
   */
  export type SimulationUpdateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Simulation
     */
    select?: SimulationSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Simulation
     */
    omit?: SimulationOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: SimulationInclude<ExtArgs> | null
    /**
     * The data needed to update a Simulation.
     */
    data: XOR<SimulationUpdateInput, SimulationUncheckedUpdateInput>
    /**
     * Choose, which Simulation to update.
     */
    where: SimulationWhereUniqueInput
  }

  /**
   * Simulation updateMany
   */
  export type SimulationUpdateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to update Simulations.
     */
    data: XOR<SimulationUpdateManyMutationInput, SimulationUncheckedUpdateManyInput>
    /**
     * Filter which Simulations to update
     */
    where?: SimulationWhereInput
    /**
     * Limit how many Simulations to update.
     */
    limit?: number
  }

  /**
   * Simulation updateManyAndReturn
   */
  export type SimulationUpdateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Simulation
     */
    select?: SimulationSelectUpdateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the Simulation
     */
    omit?: SimulationOmit<ExtArgs> | null
    /**
     * The data used to update Simulations.
     */
    data: XOR<SimulationUpdateManyMutationInput, SimulationUncheckedUpdateManyInput>
    /**
     * Filter which Simulations to update
     */
    where?: SimulationWhereInput
    /**
     * Limit how many Simulations to update.
     */
    limit?: number
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: SimulationIncludeUpdateManyAndReturn<ExtArgs> | null
  }

  /**
   * Simulation upsert
   */
  export type SimulationUpsertArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Simulation
     */
    select?: SimulationSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Simulation
     */
    omit?: SimulationOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: SimulationInclude<ExtArgs> | null
    /**
     * The filter to search for the Simulation to update in case it exists.
     */
    where: SimulationWhereUniqueInput
    /**
     * In case the Simulation found by the `where` argument doesn't exist, create a new Simulation with this data.
     */
    create: XOR<SimulationCreateInput, SimulationUncheckedCreateInput>
    /**
     * In case the Simulation was found with the provided `where` argument, update it with this data.
     */
    update: XOR<SimulationUpdateInput, SimulationUncheckedUpdateInput>
  }

  /**
   * Simulation delete
   */
  export type SimulationDeleteArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Simulation
     */
    select?: SimulationSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Simulation
     */
    omit?: SimulationOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: SimulationInclude<ExtArgs> | null
    /**
     * Filter which Simulation to delete.
     */
    where: SimulationWhereUniqueInput
  }

  /**
   * Simulation deleteMany
   */
  export type SimulationDeleteManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which Simulations to delete
     */
    where?: SimulationWhereInput
    /**
     * Limit how many Simulations to delete.
     */
    limit?: number
  }

  /**
   * Simulation.BiasDetectionResult
   */
  export type Simulation$BiasDetectionResultArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the BiasDetectionResult
     */
    select?: BiasDetectionResultSelect<ExtArgs> | null
    /**
     * Omit specific fields from the BiasDetectionResult
     */
    omit?: BiasDetectionResultOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: BiasDetectionResultInclude<ExtArgs> | null
    where?: BiasDetectionResultWhereInput
    orderBy?: BiasDetectionResultOrderByWithRelationInput | BiasDetectionResultOrderByWithRelationInput[]
    cursor?: BiasDetectionResultWhereUniqueInput
    take?: number
    skip?: number
    distinct?: BiasDetectionResultScalarFieldEnum | BiasDetectionResultScalarFieldEnum[]
  }

  /**
   * Simulation.FairnessAssessment
   */
  export type Simulation$FairnessAssessmentArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FairnessAssessment
     */
    select?: FairnessAssessmentSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FairnessAssessment
     */
    omit?: FairnessAssessmentOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FairnessAssessmentInclude<ExtArgs> | null
    where?: FairnessAssessmentWhereInput
    orderBy?: FairnessAssessmentOrderByWithRelationInput | FairnessAssessmentOrderByWithRelationInput[]
    cursor?: FairnessAssessmentWhereUniqueInput
    take?: number
    skip?: number
    distinct?: FairnessAssessmentScalarFieldEnum | FairnessAssessmentScalarFieldEnum[]
  }

  /**
   * Simulation.ExplainabilityAnalysis
   */
  export type Simulation$ExplainabilityAnalysisArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the ExplainabilityAnalysis
     */
    select?: ExplainabilityAnalysisSelect<ExtArgs> | null
    /**
     * Omit specific fields from the ExplainabilityAnalysis
     */
    omit?: ExplainabilityAnalysisOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: ExplainabilityAnalysisInclude<ExtArgs> | null
    where?: ExplainabilityAnalysisWhereInput
    orderBy?: ExplainabilityAnalysisOrderByWithRelationInput | ExplainabilityAnalysisOrderByWithRelationInput[]
    cursor?: ExplainabilityAnalysisWhereUniqueInput
    take?: number
    skip?: number
    distinct?: ExplainabilityAnalysisScalarFieldEnum | ExplainabilityAnalysisScalarFieldEnum[]
  }

  /**
   * Simulation.ComplianceRecord
   */
  export type Simulation$ComplianceRecordArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the ComplianceRecord
     */
    select?: ComplianceRecordSelect<ExtArgs> | null
    /**
     * Omit specific fields from the ComplianceRecord
     */
    omit?: ComplianceRecordOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: ComplianceRecordInclude<ExtArgs> | null
    where?: ComplianceRecordWhereInput
    orderBy?: ComplianceRecordOrderByWithRelationInput | ComplianceRecordOrderByWithRelationInput[]
    cursor?: ComplianceRecordWhereUniqueInput
    take?: number
    skip?: number
    distinct?: ComplianceRecordScalarFieldEnum | ComplianceRecordScalarFieldEnum[]
  }

  /**
   * Simulation.RiskAssessment
   */
  export type Simulation$RiskAssessmentArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the RiskAssessment
     */
    select?: RiskAssessmentSelect<ExtArgs> | null
    /**
     * Omit specific fields from the RiskAssessment
     */
    omit?: RiskAssessmentOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: RiskAssessmentInclude<ExtArgs> | null
    where?: RiskAssessmentWhereInput
    orderBy?: RiskAssessmentOrderByWithRelationInput | RiskAssessmentOrderByWithRelationInput[]
    cursor?: RiskAssessmentWhereUniqueInput
    take?: number
    skip?: number
    distinct?: RiskAssessmentScalarFieldEnum | RiskAssessmentScalarFieldEnum[]
  }

  /**
   * Simulation.auditLogs
   */
  export type Simulation$auditLogsArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the AuditLog
     */
    select?: AuditLogSelect<ExtArgs> | null
    /**
     * Omit specific fields from the AuditLog
     */
    omit?: AuditLogOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: AuditLogInclude<ExtArgs> | null
    where?: AuditLogWhereInput
    orderBy?: AuditLogOrderByWithRelationInput | AuditLogOrderByWithRelationInput[]
    cursor?: AuditLogWhereUniqueInput
    take?: number
    skip?: number
    distinct?: AuditLogScalarFieldEnum | AuditLogScalarFieldEnum[]
  }

  /**
   * Simulation without action
   */
  export type SimulationDefaultArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Simulation
     */
    select?: SimulationSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Simulation
     */
    omit?: SimulationOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: SimulationInclude<ExtArgs> | null
  }


  /**
   * Model BiasDetectionResult
   */

  export type AggregateBiasDetectionResult = {
    _count: BiasDetectionResultCountAggregateOutputType | null
    _avg: BiasDetectionResultAvgAggregateOutputType | null
    _sum: BiasDetectionResultSumAggregateOutputType | null
    _min: BiasDetectionResultMinAggregateOutputType | null
    _max: BiasDetectionResultMaxAggregateOutputType | null
  }

  export type BiasDetectionResultAvgAggregateOutputType = {
    id: number | null
    simulationId: number | null
  }

  export type BiasDetectionResultSumAggregateOutputType = {
    id: number | null
    simulationId: number | null
  }

  export type BiasDetectionResultMinAggregateOutputType = {
    id: number | null
    createdAt: Date | null
    updatedAt: Date | null
    simulationId: number | null
  }

  export type BiasDetectionResultMaxAggregateOutputType = {
    id: number | null
    createdAt: Date | null
    updatedAt: Date | null
    simulationId: number | null
  }

  export type BiasDetectionResultCountAggregateOutputType = {
    id: number
    createdAt: number
    updatedAt: number
    simulationId: number
    result: number
    _all: number
  }


  export type BiasDetectionResultAvgAggregateInputType = {
    id?: true
    simulationId?: true
  }

  export type BiasDetectionResultSumAggregateInputType = {
    id?: true
    simulationId?: true
  }

  export type BiasDetectionResultMinAggregateInputType = {
    id?: true
    createdAt?: true
    updatedAt?: true
    simulationId?: true
  }

  export type BiasDetectionResultMaxAggregateInputType = {
    id?: true
    createdAt?: true
    updatedAt?: true
    simulationId?: true
  }

  export type BiasDetectionResultCountAggregateInputType = {
    id?: true
    createdAt?: true
    updatedAt?: true
    simulationId?: true
    result?: true
    _all?: true
  }

  export type BiasDetectionResultAggregateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which BiasDetectionResult to aggregate.
     */
    where?: BiasDetectionResultWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of BiasDetectionResults to fetch.
     */
    orderBy?: BiasDetectionResultOrderByWithRelationInput | BiasDetectionResultOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the start position
     */
    cursor?: BiasDetectionResultWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` BiasDetectionResults from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` BiasDetectionResults.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Count returned BiasDetectionResults
    **/
    _count?: true | BiasDetectionResultCountAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to average
    **/
    _avg?: BiasDetectionResultAvgAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to sum
    **/
    _sum?: BiasDetectionResultSumAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the minimum value
    **/
    _min?: BiasDetectionResultMinAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the maximum value
    **/
    _max?: BiasDetectionResultMaxAggregateInputType
  }

  export type GetBiasDetectionResultAggregateType<T extends BiasDetectionResultAggregateArgs> = {
        [P in keyof T & keyof AggregateBiasDetectionResult]: P extends '_count' | 'count'
      ? T[P] extends true
        ? number
        : GetScalarType<T[P], AggregateBiasDetectionResult[P]>
      : GetScalarType<T[P], AggregateBiasDetectionResult[P]>
  }




  export type BiasDetectionResultGroupByArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: BiasDetectionResultWhereInput
    orderBy?: BiasDetectionResultOrderByWithAggregationInput | BiasDetectionResultOrderByWithAggregationInput[]
    by: BiasDetectionResultScalarFieldEnum[] | BiasDetectionResultScalarFieldEnum
    having?: BiasDetectionResultScalarWhereWithAggregatesInput
    take?: number
    skip?: number
    _count?: BiasDetectionResultCountAggregateInputType | true
    _avg?: BiasDetectionResultAvgAggregateInputType
    _sum?: BiasDetectionResultSumAggregateInputType
    _min?: BiasDetectionResultMinAggregateInputType
    _max?: BiasDetectionResultMaxAggregateInputType
  }

  export type BiasDetectionResultGroupByOutputType = {
    id: number
    createdAt: Date
    updatedAt: Date
    simulationId: number
    result: JsonValue
    _count: BiasDetectionResultCountAggregateOutputType | null
    _avg: BiasDetectionResultAvgAggregateOutputType | null
    _sum: BiasDetectionResultSumAggregateOutputType | null
    _min: BiasDetectionResultMinAggregateOutputType | null
    _max: BiasDetectionResultMaxAggregateOutputType | null
  }

  type GetBiasDetectionResultGroupByPayload<T extends BiasDetectionResultGroupByArgs> = Prisma.PrismaPromise<
    Array<
      PickEnumerable<BiasDetectionResultGroupByOutputType, T['by']> &
        {
          [P in ((keyof T) & (keyof BiasDetectionResultGroupByOutputType))]: P extends '_count'
            ? T[P] extends boolean
              ? number
              : GetScalarType<T[P], BiasDetectionResultGroupByOutputType[P]>
            : GetScalarType<T[P], BiasDetectionResultGroupByOutputType[P]>
        }
      >
    >


  export type BiasDetectionResultSelect<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    simulationId?: boolean
    result?: boolean
    simulation?: boolean | SimulationDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["biasDetectionResult"]>

  export type BiasDetectionResultSelectCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    simulationId?: boolean
    result?: boolean
    simulation?: boolean | SimulationDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["biasDetectionResult"]>

  export type BiasDetectionResultSelectUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    simulationId?: boolean
    result?: boolean
    simulation?: boolean | SimulationDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["biasDetectionResult"]>

  export type BiasDetectionResultSelectScalar = {
    id?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    simulationId?: boolean
    result?: boolean
  }

  export type BiasDetectionResultOmit<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetOmit<"id" | "createdAt" | "updatedAt" | "simulationId" | "result", ExtArgs["result"]["biasDetectionResult"]>
  export type BiasDetectionResultInclude<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    simulation?: boolean | SimulationDefaultArgs<ExtArgs>
  }
  export type BiasDetectionResultIncludeCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    simulation?: boolean | SimulationDefaultArgs<ExtArgs>
  }
  export type BiasDetectionResultIncludeUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    simulation?: boolean | SimulationDefaultArgs<ExtArgs>
  }

  export type $BiasDetectionResultPayload<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    name: "BiasDetectionResult"
    objects: {
      simulation: Prisma.$SimulationPayload<ExtArgs>
    }
    scalars: $Extensions.GetPayloadResult<{
      id: number
      createdAt: Date
      updatedAt: Date
      simulationId: number
      result: Prisma.JsonValue
    }, ExtArgs["result"]["biasDetectionResult"]>
    composites: {}
  }

  type BiasDetectionResultGetPayload<S extends boolean | null | undefined | BiasDetectionResultDefaultArgs> = $Result.GetResult<Prisma.$BiasDetectionResultPayload, S>

  type BiasDetectionResultCountArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> =
    Omit<BiasDetectionResultFindManyArgs, 'select' | 'include' | 'distinct' | 'omit'> & {
      select?: BiasDetectionResultCountAggregateInputType | true
    }

  export interface BiasDetectionResultDelegate<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> {
    [K: symbol]: { types: Prisma.TypeMap<ExtArgs>['model']['BiasDetectionResult'], meta: { name: 'BiasDetectionResult' } }
    /**
     * Find zero or one BiasDetectionResult that matches the filter.
     * @param {BiasDetectionResultFindUniqueArgs} args - Arguments to find a BiasDetectionResult
     * @example
     * // Get one BiasDetectionResult
     * const biasDetectionResult = await prisma.biasDetectionResult.findUnique({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUnique<T extends BiasDetectionResultFindUniqueArgs>(args: SelectSubset<T, BiasDetectionResultFindUniqueArgs<ExtArgs>>): Prisma__BiasDetectionResultClient<$Result.GetResult<Prisma.$BiasDetectionResultPayload<ExtArgs>, T, "findUnique", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find one BiasDetectionResult that matches the filter or throw an error with `error.code='P2025'`
     * if no matches were found.
     * @param {BiasDetectionResultFindUniqueOrThrowArgs} args - Arguments to find a BiasDetectionResult
     * @example
     * // Get one BiasDetectionResult
     * const biasDetectionResult = await prisma.biasDetectionResult.findUniqueOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUniqueOrThrow<T extends BiasDetectionResultFindUniqueOrThrowArgs>(args: SelectSubset<T, BiasDetectionResultFindUniqueOrThrowArgs<ExtArgs>>): Prisma__BiasDetectionResultClient<$Result.GetResult<Prisma.$BiasDetectionResultPayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first BiasDetectionResult that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {BiasDetectionResultFindFirstArgs} args - Arguments to find a BiasDetectionResult
     * @example
     * // Get one BiasDetectionResult
     * const biasDetectionResult = await prisma.biasDetectionResult.findFirst({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirst<T extends BiasDetectionResultFindFirstArgs>(args?: SelectSubset<T, BiasDetectionResultFindFirstArgs<ExtArgs>>): Prisma__BiasDetectionResultClient<$Result.GetResult<Prisma.$BiasDetectionResultPayload<ExtArgs>, T, "findFirst", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first BiasDetectionResult that matches the filter or
     * throw `PrismaKnownClientError` with `P2025` code if no matches were found.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {BiasDetectionResultFindFirstOrThrowArgs} args - Arguments to find a BiasDetectionResult
     * @example
     * // Get one BiasDetectionResult
     * const biasDetectionResult = await prisma.biasDetectionResult.findFirstOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirstOrThrow<T extends BiasDetectionResultFindFirstOrThrowArgs>(args?: SelectSubset<T, BiasDetectionResultFindFirstOrThrowArgs<ExtArgs>>): Prisma__BiasDetectionResultClient<$Result.GetResult<Prisma.$BiasDetectionResultPayload<ExtArgs>, T, "findFirstOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find zero or more BiasDetectionResults that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {BiasDetectionResultFindManyArgs} args - Arguments to filter and select certain fields only.
     * @example
     * // Get all BiasDetectionResults
     * const biasDetectionResults = await prisma.biasDetectionResult.findMany()
     * 
     * // Get first 10 BiasDetectionResults
     * const biasDetectionResults = await prisma.biasDetectionResult.findMany({ take: 10 })
     * 
     * // Only select the `id`
     * const biasDetectionResultWithIdOnly = await prisma.biasDetectionResult.findMany({ select: { id: true } })
     * 
     */
    findMany<T extends BiasDetectionResultFindManyArgs>(args?: SelectSubset<T, BiasDetectionResultFindManyArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$BiasDetectionResultPayload<ExtArgs>, T, "findMany", GlobalOmitOptions>>

    /**
     * Create a BiasDetectionResult.
     * @param {BiasDetectionResultCreateArgs} args - Arguments to create a BiasDetectionResult.
     * @example
     * // Create one BiasDetectionResult
     * const BiasDetectionResult = await prisma.biasDetectionResult.create({
     *   data: {
     *     // ... data to create a BiasDetectionResult
     *   }
     * })
     * 
     */
    create<T extends BiasDetectionResultCreateArgs>(args: SelectSubset<T, BiasDetectionResultCreateArgs<ExtArgs>>): Prisma__BiasDetectionResultClient<$Result.GetResult<Prisma.$BiasDetectionResultPayload<ExtArgs>, T, "create", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Create many BiasDetectionResults.
     * @param {BiasDetectionResultCreateManyArgs} args - Arguments to create many BiasDetectionResults.
     * @example
     * // Create many BiasDetectionResults
     * const biasDetectionResult = await prisma.biasDetectionResult.createMany({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     *     
     */
    createMany<T extends BiasDetectionResultCreateManyArgs>(args?: SelectSubset<T, BiasDetectionResultCreateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Create many BiasDetectionResults and returns the data saved in the database.
     * @param {BiasDetectionResultCreateManyAndReturnArgs} args - Arguments to create many BiasDetectionResults.
     * @example
     * // Create many BiasDetectionResults
     * const biasDetectionResult = await prisma.biasDetectionResult.createManyAndReturn({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Create many BiasDetectionResults and only return the `id`
     * const biasDetectionResultWithIdOnly = await prisma.biasDetectionResult.createManyAndReturn({
     *   select: { id: true },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    createManyAndReturn<T extends BiasDetectionResultCreateManyAndReturnArgs>(args?: SelectSubset<T, BiasDetectionResultCreateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$BiasDetectionResultPayload<ExtArgs>, T, "createManyAndReturn", GlobalOmitOptions>>

    /**
     * Delete a BiasDetectionResult.
     * @param {BiasDetectionResultDeleteArgs} args - Arguments to delete one BiasDetectionResult.
     * @example
     * // Delete one BiasDetectionResult
     * const BiasDetectionResult = await prisma.biasDetectionResult.delete({
     *   where: {
     *     // ... filter to delete one BiasDetectionResult
     *   }
     * })
     * 
     */
    delete<T extends BiasDetectionResultDeleteArgs>(args: SelectSubset<T, BiasDetectionResultDeleteArgs<ExtArgs>>): Prisma__BiasDetectionResultClient<$Result.GetResult<Prisma.$BiasDetectionResultPayload<ExtArgs>, T, "delete", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Update one BiasDetectionResult.
     * @param {BiasDetectionResultUpdateArgs} args - Arguments to update one BiasDetectionResult.
     * @example
     * // Update one BiasDetectionResult
     * const biasDetectionResult = await prisma.biasDetectionResult.update({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    update<T extends BiasDetectionResultUpdateArgs>(args: SelectSubset<T, BiasDetectionResultUpdateArgs<ExtArgs>>): Prisma__BiasDetectionResultClient<$Result.GetResult<Prisma.$BiasDetectionResultPayload<ExtArgs>, T, "update", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Delete zero or more BiasDetectionResults.
     * @param {BiasDetectionResultDeleteManyArgs} args - Arguments to filter BiasDetectionResults to delete.
     * @example
     * // Delete a few BiasDetectionResults
     * const { count } = await prisma.biasDetectionResult.deleteMany({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     * 
     */
    deleteMany<T extends BiasDetectionResultDeleteManyArgs>(args?: SelectSubset<T, BiasDetectionResultDeleteManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more BiasDetectionResults.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {BiasDetectionResultUpdateManyArgs} args - Arguments to update one or more rows.
     * @example
     * // Update many BiasDetectionResults
     * const biasDetectionResult = await prisma.biasDetectionResult.updateMany({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    updateMany<T extends BiasDetectionResultUpdateManyArgs>(args: SelectSubset<T, BiasDetectionResultUpdateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more BiasDetectionResults and returns the data updated in the database.
     * @param {BiasDetectionResultUpdateManyAndReturnArgs} args - Arguments to update many BiasDetectionResults.
     * @example
     * // Update many BiasDetectionResults
     * const biasDetectionResult = await prisma.biasDetectionResult.updateManyAndReturn({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Update zero or more BiasDetectionResults and only return the `id`
     * const biasDetectionResultWithIdOnly = await prisma.biasDetectionResult.updateManyAndReturn({
     *   select: { id: true },
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    updateManyAndReturn<T extends BiasDetectionResultUpdateManyAndReturnArgs>(args: SelectSubset<T, BiasDetectionResultUpdateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$BiasDetectionResultPayload<ExtArgs>, T, "updateManyAndReturn", GlobalOmitOptions>>

    /**
     * Create or update one BiasDetectionResult.
     * @param {BiasDetectionResultUpsertArgs} args - Arguments to update or create a BiasDetectionResult.
     * @example
     * // Update or create a BiasDetectionResult
     * const biasDetectionResult = await prisma.biasDetectionResult.upsert({
     *   create: {
     *     // ... data to create a BiasDetectionResult
     *   },
     *   update: {
     *     // ... in case it already exists, update
     *   },
     *   where: {
     *     // ... the filter for the BiasDetectionResult we want to update
     *   }
     * })
     */
    upsert<T extends BiasDetectionResultUpsertArgs>(args: SelectSubset<T, BiasDetectionResultUpsertArgs<ExtArgs>>): Prisma__BiasDetectionResultClient<$Result.GetResult<Prisma.$BiasDetectionResultPayload<ExtArgs>, T, "upsert", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>


    /**
     * Count the number of BiasDetectionResults.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {BiasDetectionResultCountArgs} args - Arguments to filter BiasDetectionResults to count.
     * @example
     * // Count the number of BiasDetectionResults
     * const count = await prisma.biasDetectionResult.count({
     *   where: {
     *     // ... the filter for the BiasDetectionResults we want to count
     *   }
     * })
    **/
    count<T extends BiasDetectionResultCountArgs>(
      args?: Subset<T, BiasDetectionResultCountArgs>,
    ): Prisma.PrismaPromise<
      T extends $Utils.Record<'select', any>
        ? T['select'] extends true
          ? number
          : GetScalarType<T['select'], BiasDetectionResultCountAggregateOutputType>
        : number
    >

    /**
     * Allows you to perform aggregations operations on a BiasDetectionResult.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {BiasDetectionResultAggregateArgs} args - Select which aggregations you would like to apply and on what fields.
     * @example
     * // Ordered by age ascending
     * // Where email contains prisma.io
     * // Limited to the 10 users
     * const aggregations = await prisma.user.aggregate({
     *   _avg: {
     *     age: true,
     *   },
     *   where: {
     *     email: {
     *       contains: "prisma.io",
     *     },
     *   },
     *   orderBy: {
     *     age: "asc",
     *   },
     *   take: 10,
     * })
    **/
    aggregate<T extends BiasDetectionResultAggregateArgs>(args: Subset<T, BiasDetectionResultAggregateArgs>): Prisma.PrismaPromise<GetBiasDetectionResultAggregateType<T>>

    /**
     * Group by BiasDetectionResult.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {BiasDetectionResultGroupByArgs} args - Group by arguments.
     * @example
     * // Group by city, order by createdAt, get count
     * const result = await prisma.user.groupBy({
     *   by: ['city', 'createdAt'],
     *   orderBy: {
     *     createdAt: true
     *   },
     *   _count: {
     *     _all: true
     *   },
     * })
     * 
    **/
    groupBy<
      T extends BiasDetectionResultGroupByArgs,
      HasSelectOrTake extends Or<
        Extends<'skip', Keys<T>>,
        Extends<'take', Keys<T>>
      >,
      OrderByArg extends True extends HasSelectOrTake
        ? { orderBy: BiasDetectionResultGroupByArgs['orderBy'] }
        : { orderBy?: BiasDetectionResultGroupByArgs['orderBy'] },
      OrderFields extends ExcludeUnderscoreKeys<Keys<MaybeTupleToUnion<T['orderBy']>>>,
      ByFields extends MaybeTupleToUnion<T['by']>,
      ByValid extends Has<ByFields, OrderFields>,
      HavingFields extends GetHavingFields<T['having']>,
      HavingValid extends Has<ByFields, HavingFields>,
      ByEmpty extends T['by'] extends never[] ? True : False,
      InputErrors extends ByEmpty extends True
      ? `Error: "by" must not be empty.`
      : HavingValid extends False
      ? {
          [P in HavingFields]: P extends ByFields
            ? never
            : P extends string
            ? `Error: Field "${P}" used in "having" needs to be provided in "by".`
            : [
                Error,
                'Field ',
                P,
                ` in "having" needs to be provided in "by"`,
              ]
        }[HavingFields]
      : 'take' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "take", you also need to provide "orderBy"'
      : 'skip' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "skip", you also need to provide "orderBy"'
      : ByValid extends True
      ? {}
      : {
          [P in OrderFields]: P extends ByFields
            ? never
            : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
        }[OrderFields]
    >(args: SubsetIntersection<T, BiasDetectionResultGroupByArgs, OrderByArg> & InputErrors): {} extends InputErrors ? GetBiasDetectionResultGroupByPayload<T> : Prisma.PrismaPromise<InputErrors>
  /**
   * Fields of the BiasDetectionResult model
   */
  readonly fields: BiasDetectionResultFieldRefs;
  }

  /**
   * The delegate class that acts as a "Promise-like" for BiasDetectionResult.
   * Why is this prefixed with `Prisma__`?
   * Because we want to prevent naming conflicts as mentioned in
   * https://github.com/prisma/prisma-client-js/issues/707
   */
  export interface Prisma__BiasDetectionResultClient<T, Null = never, ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> extends Prisma.PrismaPromise<T> {
    readonly [Symbol.toStringTag]: "PrismaPromise"
    simulation<T extends SimulationDefaultArgs<ExtArgs> = {}>(args?: Subset<T, SimulationDefaultArgs<ExtArgs>>): Prisma__SimulationClient<$Result.GetResult<Prisma.$SimulationPayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions> | Null, Null, ExtArgs, GlobalOmitOptions>
    /**
     * Attaches callbacks for the resolution and/or rejection of the Promise.
     * @param onfulfilled The callback to execute when the Promise is resolved.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of which ever callback is executed.
     */
    then<TResult1 = T, TResult2 = never>(onfulfilled?: ((value: T) => TResult1 | PromiseLike<TResult1>) | undefined | null, onrejected?: ((reason: any) => TResult2 | PromiseLike<TResult2>) | undefined | null): $Utils.JsPromise<TResult1 | TResult2>
    /**
     * Attaches a callback for only the rejection of the Promise.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of the callback.
     */
    catch<TResult = never>(onrejected?: ((reason: any) => TResult | PromiseLike<TResult>) | undefined | null): $Utils.JsPromise<T | TResult>
    /**
     * Attaches a callback that is invoked when the Promise is settled (fulfilled or rejected). The
     * resolved value cannot be modified from the callback.
     * @param onfinally The callback to execute when the Promise is settled (fulfilled or rejected).
     * @returns A Promise for the completion of the callback.
     */
    finally(onfinally?: (() => void) | undefined | null): $Utils.JsPromise<T>
  }




  /**
   * Fields of the BiasDetectionResult model
   */
  interface BiasDetectionResultFieldRefs {
    readonly id: FieldRef<"BiasDetectionResult", 'Int'>
    readonly createdAt: FieldRef<"BiasDetectionResult", 'DateTime'>
    readonly updatedAt: FieldRef<"BiasDetectionResult", 'DateTime'>
    readonly simulationId: FieldRef<"BiasDetectionResult", 'Int'>
    readonly result: FieldRef<"BiasDetectionResult", 'Json'>
  }
    

  // Custom InputTypes
  /**
   * BiasDetectionResult findUnique
   */
  export type BiasDetectionResultFindUniqueArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the BiasDetectionResult
     */
    select?: BiasDetectionResultSelect<ExtArgs> | null
    /**
     * Omit specific fields from the BiasDetectionResult
     */
    omit?: BiasDetectionResultOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: BiasDetectionResultInclude<ExtArgs> | null
    /**
     * Filter, which BiasDetectionResult to fetch.
     */
    where: BiasDetectionResultWhereUniqueInput
  }

  /**
   * BiasDetectionResult findUniqueOrThrow
   */
  export type BiasDetectionResultFindUniqueOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the BiasDetectionResult
     */
    select?: BiasDetectionResultSelect<ExtArgs> | null
    /**
     * Omit specific fields from the BiasDetectionResult
     */
    omit?: BiasDetectionResultOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: BiasDetectionResultInclude<ExtArgs> | null
    /**
     * Filter, which BiasDetectionResult to fetch.
     */
    where: BiasDetectionResultWhereUniqueInput
  }

  /**
   * BiasDetectionResult findFirst
   */
  export type BiasDetectionResultFindFirstArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the BiasDetectionResult
     */
    select?: BiasDetectionResultSelect<ExtArgs> | null
    /**
     * Omit specific fields from the BiasDetectionResult
     */
    omit?: BiasDetectionResultOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: BiasDetectionResultInclude<ExtArgs> | null
    /**
     * Filter, which BiasDetectionResult to fetch.
     */
    where?: BiasDetectionResultWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of BiasDetectionResults to fetch.
     */
    orderBy?: BiasDetectionResultOrderByWithRelationInput | BiasDetectionResultOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for BiasDetectionResults.
     */
    cursor?: BiasDetectionResultWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` BiasDetectionResults from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` BiasDetectionResults.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of BiasDetectionResults.
     */
    distinct?: BiasDetectionResultScalarFieldEnum | BiasDetectionResultScalarFieldEnum[]
  }

  /**
   * BiasDetectionResult findFirstOrThrow
   */
  export type BiasDetectionResultFindFirstOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the BiasDetectionResult
     */
    select?: BiasDetectionResultSelect<ExtArgs> | null
    /**
     * Omit specific fields from the BiasDetectionResult
     */
    omit?: BiasDetectionResultOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: BiasDetectionResultInclude<ExtArgs> | null
    /**
     * Filter, which BiasDetectionResult to fetch.
     */
    where?: BiasDetectionResultWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of BiasDetectionResults to fetch.
     */
    orderBy?: BiasDetectionResultOrderByWithRelationInput | BiasDetectionResultOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for BiasDetectionResults.
     */
    cursor?: BiasDetectionResultWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` BiasDetectionResults from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` BiasDetectionResults.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of BiasDetectionResults.
     */
    distinct?: BiasDetectionResultScalarFieldEnum | BiasDetectionResultScalarFieldEnum[]
  }

  /**
   * BiasDetectionResult findMany
   */
  export type BiasDetectionResultFindManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the BiasDetectionResult
     */
    select?: BiasDetectionResultSelect<ExtArgs> | null
    /**
     * Omit specific fields from the BiasDetectionResult
     */
    omit?: BiasDetectionResultOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: BiasDetectionResultInclude<ExtArgs> | null
    /**
     * Filter, which BiasDetectionResults to fetch.
     */
    where?: BiasDetectionResultWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of BiasDetectionResults to fetch.
     */
    orderBy?: BiasDetectionResultOrderByWithRelationInput | BiasDetectionResultOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for listing BiasDetectionResults.
     */
    cursor?: BiasDetectionResultWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` BiasDetectionResults from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` BiasDetectionResults.
     */
    skip?: number
    distinct?: BiasDetectionResultScalarFieldEnum | BiasDetectionResultScalarFieldEnum[]
  }

  /**
   * BiasDetectionResult create
   */
  export type BiasDetectionResultCreateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the BiasDetectionResult
     */
    select?: BiasDetectionResultSelect<ExtArgs> | null
    /**
     * Omit specific fields from the BiasDetectionResult
     */
    omit?: BiasDetectionResultOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: BiasDetectionResultInclude<ExtArgs> | null
    /**
     * The data needed to create a BiasDetectionResult.
     */
    data: XOR<BiasDetectionResultCreateInput, BiasDetectionResultUncheckedCreateInput>
  }

  /**
   * BiasDetectionResult createMany
   */
  export type BiasDetectionResultCreateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to create many BiasDetectionResults.
     */
    data: BiasDetectionResultCreateManyInput | BiasDetectionResultCreateManyInput[]
    skipDuplicates?: boolean
  }

  /**
   * BiasDetectionResult createManyAndReturn
   */
  export type BiasDetectionResultCreateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the BiasDetectionResult
     */
    select?: BiasDetectionResultSelectCreateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the BiasDetectionResult
     */
    omit?: BiasDetectionResultOmit<ExtArgs> | null
    /**
     * The data used to create many BiasDetectionResults.
     */
    data: BiasDetectionResultCreateManyInput | BiasDetectionResultCreateManyInput[]
    skipDuplicates?: boolean
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: BiasDetectionResultIncludeCreateManyAndReturn<ExtArgs> | null
  }

  /**
   * BiasDetectionResult update
   */
  export type BiasDetectionResultUpdateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the BiasDetectionResult
     */
    select?: BiasDetectionResultSelect<ExtArgs> | null
    /**
     * Omit specific fields from the BiasDetectionResult
     */
    omit?: BiasDetectionResultOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: BiasDetectionResultInclude<ExtArgs> | null
    /**
     * The data needed to update a BiasDetectionResult.
     */
    data: XOR<BiasDetectionResultUpdateInput, BiasDetectionResultUncheckedUpdateInput>
    /**
     * Choose, which BiasDetectionResult to update.
     */
    where: BiasDetectionResultWhereUniqueInput
  }

  /**
   * BiasDetectionResult updateMany
   */
  export type BiasDetectionResultUpdateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to update BiasDetectionResults.
     */
    data: XOR<BiasDetectionResultUpdateManyMutationInput, BiasDetectionResultUncheckedUpdateManyInput>
    /**
     * Filter which BiasDetectionResults to update
     */
    where?: BiasDetectionResultWhereInput
    /**
     * Limit how many BiasDetectionResults to update.
     */
    limit?: number
  }

  /**
   * BiasDetectionResult updateManyAndReturn
   */
  export type BiasDetectionResultUpdateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the BiasDetectionResult
     */
    select?: BiasDetectionResultSelectUpdateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the BiasDetectionResult
     */
    omit?: BiasDetectionResultOmit<ExtArgs> | null
    /**
     * The data used to update BiasDetectionResults.
     */
    data: XOR<BiasDetectionResultUpdateManyMutationInput, BiasDetectionResultUncheckedUpdateManyInput>
    /**
     * Filter which BiasDetectionResults to update
     */
    where?: BiasDetectionResultWhereInput
    /**
     * Limit how many BiasDetectionResults to update.
     */
    limit?: number
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: BiasDetectionResultIncludeUpdateManyAndReturn<ExtArgs> | null
  }

  /**
   * BiasDetectionResult upsert
   */
  export type BiasDetectionResultUpsertArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the BiasDetectionResult
     */
    select?: BiasDetectionResultSelect<ExtArgs> | null
    /**
     * Omit specific fields from the BiasDetectionResult
     */
    omit?: BiasDetectionResultOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: BiasDetectionResultInclude<ExtArgs> | null
    /**
     * The filter to search for the BiasDetectionResult to update in case it exists.
     */
    where: BiasDetectionResultWhereUniqueInput
    /**
     * In case the BiasDetectionResult found by the `where` argument doesn't exist, create a new BiasDetectionResult with this data.
     */
    create: XOR<BiasDetectionResultCreateInput, BiasDetectionResultUncheckedCreateInput>
    /**
     * In case the BiasDetectionResult was found with the provided `where` argument, update it with this data.
     */
    update: XOR<BiasDetectionResultUpdateInput, BiasDetectionResultUncheckedUpdateInput>
  }

  /**
   * BiasDetectionResult delete
   */
  export type BiasDetectionResultDeleteArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the BiasDetectionResult
     */
    select?: BiasDetectionResultSelect<ExtArgs> | null
    /**
     * Omit specific fields from the BiasDetectionResult
     */
    omit?: BiasDetectionResultOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: BiasDetectionResultInclude<ExtArgs> | null
    /**
     * Filter which BiasDetectionResult to delete.
     */
    where: BiasDetectionResultWhereUniqueInput
  }

  /**
   * BiasDetectionResult deleteMany
   */
  export type BiasDetectionResultDeleteManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which BiasDetectionResults to delete
     */
    where?: BiasDetectionResultWhereInput
    /**
     * Limit how many BiasDetectionResults to delete.
     */
    limit?: number
  }

  /**
   * BiasDetectionResult without action
   */
  export type BiasDetectionResultDefaultArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the BiasDetectionResult
     */
    select?: BiasDetectionResultSelect<ExtArgs> | null
    /**
     * Omit specific fields from the BiasDetectionResult
     */
    omit?: BiasDetectionResultOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: BiasDetectionResultInclude<ExtArgs> | null
  }


  /**
   * Model FairnessAssessment
   */

  export type AggregateFairnessAssessment = {
    _count: FairnessAssessmentCountAggregateOutputType | null
    _avg: FairnessAssessmentAvgAggregateOutputType | null
    _sum: FairnessAssessmentSumAggregateOutputType | null
    _min: FairnessAssessmentMinAggregateOutputType | null
    _max: FairnessAssessmentMaxAggregateOutputType | null
  }

  export type FairnessAssessmentAvgAggregateOutputType = {
    id: number | null
    simulationId: number | null
  }

  export type FairnessAssessmentSumAggregateOutputType = {
    id: number | null
    simulationId: number | null
  }

  export type FairnessAssessmentMinAggregateOutputType = {
    id: number | null
    createdAt: Date | null
    updatedAt: Date | null
    simulationId: number | null
  }

  export type FairnessAssessmentMaxAggregateOutputType = {
    id: number | null
    createdAt: Date | null
    updatedAt: Date | null
    simulationId: number | null
  }

  export type FairnessAssessmentCountAggregateOutputType = {
    id: number
    createdAt: number
    updatedAt: number
    simulationId: number
    assessment: number
    _all: number
  }


  export type FairnessAssessmentAvgAggregateInputType = {
    id?: true
    simulationId?: true
  }

  export type FairnessAssessmentSumAggregateInputType = {
    id?: true
    simulationId?: true
  }

  export type FairnessAssessmentMinAggregateInputType = {
    id?: true
    createdAt?: true
    updatedAt?: true
    simulationId?: true
  }

  export type FairnessAssessmentMaxAggregateInputType = {
    id?: true
    createdAt?: true
    updatedAt?: true
    simulationId?: true
  }

  export type FairnessAssessmentCountAggregateInputType = {
    id?: true
    createdAt?: true
    updatedAt?: true
    simulationId?: true
    assessment?: true
    _all?: true
  }

  export type FairnessAssessmentAggregateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which FairnessAssessment to aggregate.
     */
    where?: FairnessAssessmentWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of FairnessAssessments to fetch.
     */
    orderBy?: FairnessAssessmentOrderByWithRelationInput | FairnessAssessmentOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the start position
     */
    cursor?: FairnessAssessmentWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` FairnessAssessments from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` FairnessAssessments.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Count returned FairnessAssessments
    **/
    _count?: true | FairnessAssessmentCountAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to average
    **/
    _avg?: FairnessAssessmentAvgAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to sum
    **/
    _sum?: FairnessAssessmentSumAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the minimum value
    **/
    _min?: FairnessAssessmentMinAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the maximum value
    **/
    _max?: FairnessAssessmentMaxAggregateInputType
  }

  export type GetFairnessAssessmentAggregateType<T extends FairnessAssessmentAggregateArgs> = {
        [P in keyof T & keyof AggregateFairnessAssessment]: P extends '_count' | 'count'
      ? T[P] extends true
        ? number
        : GetScalarType<T[P], AggregateFairnessAssessment[P]>
      : GetScalarType<T[P], AggregateFairnessAssessment[P]>
  }




  export type FairnessAssessmentGroupByArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: FairnessAssessmentWhereInput
    orderBy?: FairnessAssessmentOrderByWithAggregationInput | FairnessAssessmentOrderByWithAggregationInput[]
    by: FairnessAssessmentScalarFieldEnum[] | FairnessAssessmentScalarFieldEnum
    having?: FairnessAssessmentScalarWhereWithAggregatesInput
    take?: number
    skip?: number
    _count?: FairnessAssessmentCountAggregateInputType | true
    _avg?: FairnessAssessmentAvgAggregateInputType
    _sum?: FairnessAssessmentSumAggregateInputType
    _min?: FairnessAssessmentMinAggregateInputType
    _max?: FairnessAssessmentMaxAggregateInputType
  }

  export type FairnessAssessmentGroupByOutputType = {
    id: number
    createdAt: Date
    updatedAt: Date
    simulationId: number
    assessment: JsonValue
    _count: FairnessAssessmentCountAggregateOutputType | null
    _avg: FairnessAssessmentAvgAggregateOutputType | null
    _sum: FairnessAssessmentSumAggregateOutputType | null
    _min: FairnessAssessmentMinAggregateOutputType | null
    _max: FairnessAssessmentMaxAggregateOutputType | null
  }

  type GetFairnessAssessmentGroupByPayload<T extends FairnessAssessmentGroupByArgs> = Prisma.PrismaPromise<
    Array<
      PickEnumerable<FairnessAssessmentGroupByOutputType, T['by']> &
        {
          [P in ((keyof T) & (keyof FairnessAssessmentGroupByOutputType))]: P extends '_count'
            ? T[P] extends boolean
              ? number
              : GetScalarType<T[P], FairnessAssessmentGroupByOutputType[P]>
            : GetScalarType<T[P], FairnessAssessmentGroupByOutputType[P]>
        }
      >
    >


  export type FairnessAssessmentSelect<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    simulationId?: boolean
    assessment?: boolean
    simulation?: boolean | SimulationDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["fairnessAssessment"]>

  export type FairnessAssessmentSelectCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    simulationId?: boolean
    assessment?: boolean
    simulation?: boolean | SimulationDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["fairnessAssessment"]>

  export type FairnessAssessmentSelectUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    simulationId?: boolean
    assessment?: boolean
    simulation?: boolean | SimulationDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["fairnessAssessment"]>

  export type FairnessAssessmentSelectScalar = {
    id?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    simulationId?: boolean
    assessment?: boolean
  }

  export type FairnessAssessmentOmit<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetOmit<"id" | "createdAt" | "updatedAt" | "simulationId" | "assessment", ExtArgs["result"]["fairnessAssessment"]>
  export type FairnessAssessmentInclude<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    simulation?: boolean | SimulationDefaultArgs<ExtArgs>
  }
  export type FairnessAssessmentIncludeCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    simulation?: boolean | SimulationDefaultArgs<ExtArgs>
  }
  export type FairnessAssessmentIncludeUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    simulation?: boolean | SimulationDefaultArgs<ExtArgs>
  }

  export type $FairnessAssessmentPayload<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    name: "FairnessAssessment"
    objects: {
      simulation: Prisma.$SimulationPayload<ExtArgs>
    }
    scalars: $Extensions.GetPayloadResult<{
      id: number
      createdAt: Date
      updatedAt: Date
      simulationId: number
      assessment: Prisma.JsonValue
    }, ExtArgs["result"]["fairnessAssessment"]>
    composites: {}
  }

  type FairnessAssessmentGetPayload<S extends boolean | null | undefined | FairnessAssessmentDefaultArgs> = $Result.GetResult<Prisma.$FairnessAssessmentPayload, S>

  type FairnessAssessmentCountArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> =
    Omit<FairnessAssessmentFindManyArgs, 'select' | 'include' | 'distinct' | 'omit'> & {
      select?: FairnessAssessmentCountAggregateInputType | true
    }

  export interface FairnessAssessmentDelegate<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> {
    [K: symbol]: { types: Prisma.TypeMap<ExtArgs>['model']['FairnessAssessment'], meta: { name: 'FairnessAssessment' } }
    /**
     * Find zero or one FairnessAssessment that matches the filter.
     * @param {FairnessAssessmentFindUniqueArgs} args - Arguments to find a FairnessAssessment
     * @example
     * // Get one FairnessAssessment
     * const fairnessAssessment = await prisma.fairnessAssessment.findUnique({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUnique<T extends FairnessAssessmentFindUniqueArgs>(args: SelectSubset<T, FairnessAssessmentFindUniqueArgs<ExtArgs>>): Prisma__FairnessAssessmentClient<$Result.GetResult<Prisma.$FairnessAssessmentPayload<ExtArgs>, T, "findUnique", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find one FairnessAssessment that matches the filter or throw an error with `error.code='P2025'`
     * if no matches were found.
     * @param {FairnessAssessmentFindUniqueOrThrowArgs} args - Arguments to find a FairnessAssessment
     * @example
     * // Get one FairnessAssessment
     * const fairnessAssessment = await prisma.fairnessAssessment.findUniqueOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUniqueOrThrow<T extends FairnessAssessmentFindUniqueOrThrowArgs>(args: SelectSubset<T, FairnessAssessmentFindUniqueOrThrowArgs<ExtArgs>>): Prisma__FairnessAssessmentClient<$Result.GetResult<Prisma.$FairnessAssessmentPayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first FairnessAssessment that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {FairnessAssessmentFindFirstArgs} args - Arguments to find a FairnessAssessment
     * @example
     * // Get one FairnessAssessment
     * const fairnessAssessment = await prisma.fairnessAssessment.findFirst({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirst<T extends FairnessAssessmentFindFirstArgs>(args?: SelectSubset<T, FairnessAssessmentFindFirstArgs<ExtArgs>>): Prisma__FairnessAssessmentClient<$Result.GetResult<Prisma.$FairnessAssessmentPayload<ExtArgs>, T, "findFirst", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first FairnessAssessment that matches the filter or
     * throw `PrismaKnownClientError` with `P2025` code if no matches were found.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {FairnessAssessmentFindFirstOrThrowArgs} args - Arguments to find a FairnessAssessment
     * @example
     * // Get one FairnessAssessment
     * const fairnessAssessment = await prisma.fairnessAssessment.findFirstOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirstOrThrow<T extends FairnessAssessmentFindFirstOrThrowArgs>(args?: SelectSubset<T, FairnessAssessmentFindFirstOrThrowArgs<ExtArgs>>): Prisma__FairnessAssessmentClient<$Result.GetResult<Prisma.$FairnessAssessmentPayload<ExtArgs>, T, "findFirstOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find zero or more FairnessAssessments that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {FairnessAssessmentFindManyArgs} args - Arguments to filter and select certain fields only.
     * @example
     * // Get all FairnessAssessments
     * const fairnessAssessments = await prisma.fairnessAssessment.findMany()
     * 
     * // Get first 10 FairnessAssessments
     * const fairnessAssessments = await prisma.fairnessAssessment.findMany({ take: 10 })
     * 
     * // Only select the `id`
     * const fairnessAssessmentWithIdOnly = await prisma.fairnessAssessment.findMany({ select: { id: true } })
     * 
     */
    findMany<T extends FairnessAssessmentFindManyArgs>(args?: SelectSubset<T, FairnessAssessmentFindManyArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$FairnessAssessmentPayload<ExtArgs>, T, "findMany", GlobalOmitOptions>>

    /**
     * Create a FairnessAssessment.
     * @param {FairnessAssessmentCreateArgs} args - Arguments to create a FairnessAssessment.
     * @example
     * // Create one FairnessAssessment
     * const FairnessAssessment = await prisma.fairnessAssessment.create({
     *   data: {
     *     // ... data to create a FairnessAssessment
     *   }
     * })
     * 
     */
    create<T extends FairnessAssessmentCreateArgs>(args: SelectSubset<T, FairnessAssessmentCreateArgs<ExtArgs>>): Prisma__FairnessAssessmentClient<$Result.GetResult<Prisma.$FairnessAssessmentPayload<ExtArgs>, T, "create", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Create many FairnessAssessments.
     * @param {FairnessAssessmentCreateManyArgs} args - Arguments to create many FairnessAssessments.
     * @example
     * // Create many FairnessAssessments
     * const fairnessAssessment = await prisma.fairnessAssessment.createMany({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     *     
     */
    createMany<T extends FairnessAssessmentCreateManyArgs>(args?: SelectSubset<T, FairnessAssessmentCreateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Create many FairnessAssessments and returns the data saved in the database.
     * @param {FairnessAssessmentCreateManyAndReturnArgs} args - Arguments to create many FairnessAssessments.
     * @example
     * // Create many FairnessAssessments
     * const fairnessAssessment = await prisma.fairnessAssessment.createManyAndReturn({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Create many FairnessAssessments and only return the `id`
     * const fairnessAssessmentWithIdOnly = await prisma.fairnessAssessment.createManyAndReturn({
     *   select: { id: true },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    createManyAndReturn<T extends FairnessAssessmentCreateManyAndReturnArgs>(args?: SelectSubset<T, FairnessAssessmentCreateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$FairnessAssessmentPayload<ExtArgs>, T, "createManyAndReturn", GlobalOmitOptions>>

    /**
     * Delete a FairnessAssessment.
     * @param {FairnessAssessmentDeleteArgs} args - Arguments to delete one FairnessAssessment.
     * @example
     * // Delete one FairnessAssessment
     * const FairnessAssessment = await prisma.fairnessAssessment.delete({
     *   where: {
     *     // ... filter to delete one FairnessAssessment
     *   }
     * })
     * 
     */
    delete<T extends FairnessAssessmentDeleteArgs>(args: SelectSubset<T, FairnessAssessmentDeleteArgs<ExtArgs>>): Prisma__FairnessAssessmentClient<$Result.GetResult<Prisma.$FairnessAssessmentPayload<ExtArgs>, T, "delete", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Update one FairnessAssessment.
     * @param {FairnessAssessmentUpdateArgs} args - Arguments to update one FairnessAssessment.
     * @example
     * // Update one FairnessAssessment
     * const fairnessAssessment = await prisma.fairnessAssessment.update({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    update<T extends FairnessAssessmentUpdateArgs>(args: SelectSubset<T, FairnessAssessmentUpdateArgs<ExtArgs>>): Prisma__FairnessAssessmentClient<$Result.GetResult<Prisma.$FairnessAssessmentPayload<ExtArgs>, T, "update", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Delete zero or more FairnessAssessments.
     * @param {FairnessAssessmentDeleteManyArgs} args - Arguments to filter FairnessAssessments to delete.
     * @example
     * // Delete a few FairnessAssessments
     * const { count } = await prisma.fairnessAssessment.deleteMany({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     * 
     */
    deleteMany<T extends FairnessAssessmentDeleteManyArgs>(args?: SelectSubset<T, FairnessAssessmentDeleteManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more FairnessAssessments.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {FairnessAssessmentUpdateManyArgs} args - Arguments to update one or more rows.
     * @example
     * // Update many FairnessAssessments
     * const fairnessAssessment = await prisma.fairnessAssessment.updateMany({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    updateMany<T extends FairnessAssessmentUpdateManyArgs>(args: SelectSubset<T, FairnessAssessmentUpdateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more FairnessAssessments and returns the data updated in the database.
     * @param {FairnessAssessmentUpdateManyAndReturnArgs} args - Arguments to update many FairnessAssessments.
     * @example
     * // Update many FairnessAssessments
     * const fairnessAssessment = await prisma.fairnessAssessment.updateManyAndReturn({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Update zero or more FairnessAssessments and only return the `id`
     * const fairnessAssessmentWithIdOnly = await prisma.fairnessAssessment.updateManyAndReturn({
     *   select: { id: true },
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    updateManyAndReturn<T extends FairnessAssessmentUpdateManyAndReturnArgs>(args: SelectSubset<T, FairnessAssessmentUpdateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$FairnessAssessmentPayload<ExtArgs>, T, "updateManyAndReturn", GlobalOmitOptions>>

    /**
     * Create or update one FairnessAssessment.
     * @param {FairnessAssessmentUpsertArgs} args - Arguments to update or create a FairnessAssessment.
     * @example
     * // Update or create a FairnessAssessment
     * const fairnessAssessment = await prisma.fairnessAssessment.upsert({
     *   create: {
     *     // ... data to create a FairnessAssessment
     *   },
     *   update: {
     *     // ... in case it already exists, update
     *   },
     *   where: {
     *     // ... the filter for the FairnessAssessment we want to update
     *   }
     * })
     */
    upsert<T extends FairnessAssessmentUpsertArgs>(args: SelectSubset<T, FairnessAssessmentUpsertArgs<ExtArgs>>): Prisma__FairnessAssessmentClient<$Result.GetResult<Prisma.$FairnessAssessmentPayload<ExtArgs>, T, "upsert", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>


    /**
     * Count the number of FairnessAssessments.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {FairnessAssessmentCountArgs} args - Arguments to filter FairnessAssessments to count.
     * @example
     * // Count the number of FairnessAssessments
     * const count = await prisma.fairnessAssessment.count({
     *   where: {
     *     // ... the filter for the FairnessAssessments we want to count
     *   }
     * })
    **/
    count<T extends FairnessAssessmentCountArgs>(
      args?: Subset<T, FairnessAssessmentCountArgs>,
    ): Prisma.PrismaPromise<
      T extends $Utils.Record<'select', any>
        ? T['select'] extends true
          ? number
          : GetScalarType<T['select'], FairnessAssessmentCountAggregateOutputType>
        : number
    >

    /**
     * Allows you to perform aggregations operations on a FairnessAssessment.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {FairnessAssessmentAggregateArgs} args - Select which aggregations you would like to apply and on what fields.
     * @example
     * // Ordered by age ascending
     * // Where email contains prisma.io
     * // Limited to the 10 users
     * const aggregations = await prisma.user.aggregate({
     *   _avg: {
     *     age: true,
     *   },
     *   where: {
     *     email: {
     *       contains: "prisma.io",
     *     },
     *   },
     *   orderBy: {
     *     age: "asc",
     *   },
     *   take: 10,
     * })
    **/
    aggregate<T extends FairnessAssessmentAggregateArgs>(args: Subset<T, FairnessAssessmentAggregateArgs>): Prisma.PrismaPromise<GetFairnessAssessmentAggregateType<T>>

    /**
     * Group by FairnessAssessment.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {FairnessAssessmentGroupByArgs} args - Group by arguments.
     * @example
     * // Group by city, order by createdAt, get count
     * const result = await prisma.user.groupBy({
     *   by: ['city', 'createdAt'],
     *   orderBy: {
     *     createdAt: true
     *   },
     *   _count: {
     *     _all: true
     *   },
     * })
     * 
    **/
    groupBy<
      T extends FairnessAssessmentGroupByArgs,
      HasSelectOrTake extends Or<
        Extends<'skip', Keys<T>>,
        Extends<'take', Keys<T>>
      >,
      OrderByArg extends True extends HasSelectOrTake
        ? { orderBy: FairnessAssessmentGroupByArgs['orderBy'] }
        : { orderBy?: FairnessAssessmentGroupByArgs['orderBy'] },
      OrderFields extends ExcludeUnderscoreKeys<Keys<MaybeTupleToUnion<T['orderBy']>>>,
      ByFields extends MaybeTupleToUnion<T['by']>,
      ByValid extends Has<ByFields, OrderFields>,
      HavingFields extends GetHavingFields<T['having']>,
      HavingValid extends Has<ByFields, HavingFields>,
      ByEmpty extends T['by'] extends never[] ? True : False,
      InputErrors extends ByEmpty extends True
      ? `Error: "by" must not be empty.`
      : HavingValid extends False
      ? {
          [P in HavingFields]: P extends ByFields
            ? never
            : P extends string
            ? `Error: Field "${P}" used in "having" needs to be provided in "by".`
            : [
                Error,
                'Field ',
                P,
                ` in "having" needs to be provided in "by"`,
              ]
        }[HavingFields]
      : 'take' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "take", you also need to provide "orderBy"'
      : 'skip' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "skip", you also need to provide "orderBy"'
      : ByValid extends True
      ? {}
      : {
          [P in OrderFields]: P extends ByFields
            ? never
            : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
        }[OrderFields]
    >(args: SubsetIntersection<T, FairnessAssessmentGroupByArgs, OrderByArg> & InputErrors): {} extends InputErrors ? GetFairnessAssessmentGroupByPayload<T> : Prisma.PrismaPromise<InputErrors>
  /**
   * Fields of the FairnessAssessment model
   */
  readonly fields: FairnessAssessmentFieldRefs;
  }

  /**
   * The delegate class that acts as a "Promise-like" for FairnessAssessment.
   * Why is this prefixed with `Prisma__`?
   * Because we want to prevent naming conflicts as mentioned in
   * https://github.com/prisma/prisma-client-js/issues/707
   */
  export interface Prisma__FairnessAssessmentClient<T, Null = never, ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> extends Prisma.PrismaPromise<T> {
    readonly [Symbol.toStringTag]: "PrismaPromise"
    simulation<T extends SimulationDefaultArgs<ExtArgs> = {}>(args?: Subset<T, SimulationDefaultArgs<ExtArgs>>): Prisma__SimulationClient<$Result.GetResult<Prisma.$SimulationPayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions> | Null, Null, ExtArgs, GlobalOmitOptions>
    /**
     * Attaches callbacks for the resolution and/or rejection of the Promise.
     * @param onfulfilled The callback to execute when the Promise is resolved.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of which ever callback is executed.
     */
    then<TResult1 = T, TResult2 = never>(onfulfilled?: ((value: T) => TResult1 | PromiseLike<TResult1>) | undefined | null, onrejected?: ((reason: any) => TResult2 | PromiseLike<TResult2>) | undefined | null): $Utils.JsPromise<TResult1 | TResult2>
    /**
     * Attaches a callback for only the rejection of the Promise.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of the callback.
     */
    catch<TResult = never>(onrejected?: ((reason: any) => TResult | PromiseLike<TResult>) | undefined | null): $Utils.JsPromise<T | TResult>
    /**
     * Attaches a callback that is invoked when the Promise is settled (fulfilled or rejected). The
     * resolved value cannot be modified from the callback.
     * @param onfinally The callback to execute when the Promise is settled (fulfilled or rejected).
     * @returns A Promise for the completion of the callback.
     */
    finally(onfinally?: (() => void) | undefined | null): $Utils.JsPromise<T>
  }




  /**
   * Fields of the FairnessAssessment model
   */
  interface FairnessAssessmentFieldRefs {
    readonly id: FieldRef<"FairnessAssessment", 'Int'>
    readonly createdAt: FieldRef<"FairnessAssessment", 'DateTime'>
    readonly updatedAt: FieldRef<"FairnessAssessment", 'DateTime'>
    readonly simulationId: FieldRef<"FairnessAssessment", 'Int'>
    readonly assessment: FieldRef<"FairnessAssessment", 'Json'>
  }
    

  // Custom InputTypes
  /**
   * FairnessAssessment findUnique
   */
  export type FairnessAssessmentFindUniqueArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FairnessAssessment
     */
    select?: FairnessAssessmentSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FairnessAssessment
     */
    omit?: FairnessAssessmentOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FairnessAssessmentInclude<ExtArgs> | null
    /**
     * Filter, which FairnessAssessment to fetch.
     */
    where: FairnessAssessmentWhereUniqueInput
  }

  /**
   * FairnessAssessment findUniqueOrThrow
   */
  export type FairnessAssessmentFindUniqueOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FairnessAssessment
     */
    select?: FairnessAssessmentSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FairnessAssessment
     */
    omit?: FairnessAssessmentOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FairnessAssessmentInclude<ExtArgs> | null
    /**
     * Filter, which FairnessAssessment to fetch.
     */
    where: FairnessAssessmentWhereUniqueInput
  }

  /**
   * FairnessAssessment findFirst
   */
  export type FairnessAssessmentFindFirstArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FairnessAssessment
     */
    select?: FairnessAssessmentSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FairnessAssessment
     */
    omit?: FairnessAssessmentOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FairnessAssessmentInclude<ExtArgs> | null
    /**
     * Filter, which FairnessAssessment to fetch.
     */
    where?: FairnessAssessmentWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of FairnessAssessments to fetch.
     */
    orderBy?: FairnessAssessmentOrderByWithRelationInput | FairnessAssessmentOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for FairnessAssessments.
     */
    cursor?: FairnessAssessmentWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` FairnessAssessments from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` FairnessAssessments.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of FairnessAssessments.
     */
    distinct?: FairnessAssessmentScalarFieldEnum | FairnessAssessmentScalarFieldEnum[]
  }

  /**
   * FairnessAssessment findFirstOrThrow
   */
  export type FairnessAssessmentFindFirstOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FairnessAssessment
     */
    select?: FairnessAssessmentSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FairnessAssessment
     */
    omit?: FairnessAssessmentOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FairnessAssessmentInclude<ExtArgs> | null
    /**
     * Filter, which FairnessAssessment to fetch.
     */
    where?: FairnessAssessmentWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of FairnessAssessments to fetch.
     */
    orderBy?: FairnessAssessmentOrderByWithRelationInput | FairnessAssessmentOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for FairnessAssessments.
     */
    cursor?: FairnessAssessmentWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` FairnessAssessments from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` FairnessAssessments.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of FairnessAssessments.
     */
    distinct?: FairnessAssessmentScalarFieldEnum | FairnessAssessmentScalarFieldEnum[]
  }

  /**
   * FairnessAssessment findMany
   */
  export type FairnessAssessmentFindManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FairnessAssessment
     */
    select?: FairnessAssessmentSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FairnessAssessment
     */
    omit?: FairnessAssessmentOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FairnessAssessmentInclude<ExtArgs> | null
    /**
     * Filter, which FairnessAssessments to fetch.
     */
    where?: FairnessAssessmentWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of FairnessAssessments to fetch.
     */
    orderBy?: FairnessAssessmentOrderByWithRelationInput | FairnessAssessmentOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for listing FairnessAssessments.
     */
    cursor?: FairnessAssessmentWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` FairnessAssessments from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` FairnessAssessments.
     */
    skip?: number
    distinct?: FairnessAssessmentScalarFieldEnum | FairnessAssessmentScalarFieldEnum[]
  }

  /**
   * FairnessAssessment create
   */
  export type FairnessAssessmentCreateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FairnessAssessment
     */
    select?: FairnessAssessmentSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FairnessAssessment
     */
    omit?: FairnessAssessmentOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FairnessAssessmentInclude<ExtArgs> | null
    /**
     * The data needed to create a FairnessAssessment.
     */
    data: XOR<FairnessAssessmentCreateInput, FairnessAssessmentUncheckedCreateInput>
  }

  /**
   * FairnessAssessment createMany
   */
  export type FairnessAssessmentCreateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to create many FairnessAssessments.
     */
    data: FairnessAssessmentCreateManyInput | FairnessAssessmentCreateManyInput[]
    skipDuplicates?: boolean
  }

  /**
   * FairnessAssessment createManyAndReturn
   */
  export type FairnessAssessmentCreateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FairnessAssessment
     */
    select?: FairnessAssessmentSelectCreateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the FairnessAssessment
     */
    omit?: FairnessAssessmentOmit<ExtArgs> | null
    /**
     * The data used to create many FairnessAssessments.
     */
    data: FairnessAssessmentCreateManyInput | FairnessAssessmentCreateManyInput[]
    skipDuplicates?: boolean
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FairnessAssessmentIncludeCreateManyAndReturn<ExtArgs> | null
  }

  /**
   * FairnessAssessment update
   */
  export type FairnessAssessmentUpdateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FairnessAssessment
     */
    select?: FairnessAssessmentSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FairnessAssessment
     */
    omit?: FairnessAssessmentOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FairnessAssessmentInclude<ExtArgs> | null
    /**
     * The data needed to update a FairnessAssessment.
     */
    data: XOR<FairnessAssessmentUpdateInput, FairnessAssessmentUncheckedUpdateInput>
    /**
     * Choose, which FairnessAssessment to update.
     */
    where: FairnessAssessmentWhereUniqueInput
  }

  /**
   * FairnessAssessment updateMany
   */
  export type FairnessAssessmentUpdateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to update FairnessAssessments.
     */
    data: XOR<FairnessAssessmentUpdateManyMutationInput, FairnessAssessmentUncheckedUpdateManyInput>
    /**
     * Filter which FairnessAssessments to update
     */
    where?: FairnessAssessmentWhereInput
    /**
     * Limit how many FairnessAssessments to update.
     */
    limit?: number
  }

  /**
   * FairnessAssessment updateManyAndReturn
   */
  export type FairnessAssessmentUpdateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FairnessAssessment
     */
    select?: FairnessAssessmentSelectUpdateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the FairnessAssessment
     */
    omit?: FairnessAssessmentOmit<ExtArgs> | null
    /**
     * The data used to update FairnessAssessments.
     */
    data: XOR<FairnessAssessmentUpdateManyMutationInput, FairnessAssessmentUncheckedUpdateManyInput>
    /**
     * Filter which FairnessAssessments to update
     */
    where?: FairnessAssessmentWhereInput
    /**
     * Limit how many FairnessAssessments to update.
     */
    limit?: number
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FairnessAssessmentIncludeUpdateManyAndReturn<ExtArgs> | null
  }

  /**
   * FairnessAssessment upsert
   */
  export type FairnessAssessmentUpsertArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FairnessAssessment
     */
    select?: FairnessAssessmentSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FairnessAssessment
     */
    omit?: FairnessAssessmentOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FairnessAssessmentInclude<ExtArgs> | null
    /**
     * The filter to search for the FairnessAssessment to update in case it exists.
     */
    where: FairnessAssessmentWhereUniqueInput
    /**
     * In case the FairnessAssessment found by the `where` argument doesn't exist, create a new FairnessAssessment with this data.
     */
    create: XOR<FairnessAssessmentCreateInput, FairnessAssessmentUncheckedCreateInput>
    /**
     * In case the FairnessAssessment was found with the provided `where` argument, update it with this data.
     */
    update: XOR<FairnessAssessmentUpdateInput, FairnessAssessmentUncheckedUpdateInput>
  }

  /**
   * FairnessAssessment delete
   */
  export type FairnessAssessmentDeleteArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FairnessAssessment
     */
    select?: FairnessAssessmentSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FairnessAssessment
     */
    omit?: FairnessAssessmentOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FairnessAssessmentInclude<ExtArgs> | null
    /**
     * Filter which FairnessAssessment to delete.
     */
    where: FairnessAssessmentWhereUniqueInput
  }

  /**
   * FairnessAssessment deleteMany
   */
  export type FairnessAssessmentDeleteManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which FairnessAssessments to delete
     */
    where?: FairnessAssessmentWhereInput
    /**
     * Limit how many FairnessAssessments to delete.
     */
    limit?: number
  }

  /**
   * FairnessAssessment without action
   */
  export type FairnessAssessmentDefaultArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FairnessAssessment
     */
    select?: FairnessAssessmentSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FairnessAssessment
     */
    omit?: FairnessAssessmentOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FairnessAssessmentInclude<ExtArgs> | null
  }


  /**
   * Model ExplainabilityAnalysis
   */

  export type AggregateExplainabilityAnalysis = {
    _count: ExplainabilityAnalysisCountAggregateOutputType | null
    _avg: ExplainabilityAnalysisAvgAggregateOutputType | null
    _sum: ExplainabilityAnalysisSumAggregateOutputType | null
    _min: ExplainabilityAnalysisMinAggregateOutputType | null
    _max: ExplainabilityAnalysisMaxAggregateOutputType | null
  }

  export type ExplainabilityAnalysisAvgAggregateOutputType = {
    id: number | null
    simulationId: number | null
  }

  export type ExplainabilityAnalysisSumAggregateOutputType = {
    id: number | null
    simulationId: number | null
  }

  export type ExplainabilityAnalysisMinAggregateOutputType = {
    id: number | null
    createdAt: Date | null
    updatedAt: Date | null
    simulationId: number | null
  }

  export type ExplainabilityAnalysisMaxAggregateOutputType = {
    id: number | null
    createdAt: Date | null
    updatedAt: Date | null
    simulationId: number | null
  }

  export type ExplainabilityAnalysisCountAggregateOutputType = {
    id: number
    createdAt: number
    updatedAt: number
    simulationId: number
    analysis: number
    _all: number
  }


  export type ExplainabilityAnalysisAvgAggregateInputType = {
    id?: true
    simulationId?: true
  }

  export type ExplainabilityAnalysisSumAggregateInputType = {
    id?: true
    simulationId?: true
  }

  export type ExplainabilityAnalysisMinAggregateInputType = {
    id?: true
    createdAt?: true
    updatedAt?: true
    simulationId?: true
  }

  export type ExplainabilityAnalysisMaxAggregateInputType = {
    id?: true
    createdAt?: true
    updatedAt?: true
    simulationId?: true
  }

  export type ExplainabilityAnalysisCountAggregateInputType = {
    id?: true
    createdAt?: true
    updatedAt?: true
    simulationId?: true
    analysis?: true
    _all?: true
  }

  export type ExplainabilityAnalysisAggregateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which ExplainabilityAnalysis to aggregate.
     */
    where?: ExplainabilityAnalysisWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of ExplainabilityAnalyses to fetch.
     */
    orderBy?: ExplainabilityAnalysisOrderByWithRelationInput | ExplainabilityAnalysisOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the start position
     */
    cursor?: ExplainabilityAnalysisWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` ExplainabilityAnalyses from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` ExplainabilityAnalyses.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Count returned ExplainabilityAnalyses
    **/
    _count?: true | ExplainabilityAnalysisCountAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to average
    **/
    _avg?: ExplainabilityAnalysisAvgAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to sum
    **/
    _sum?: ExplainabilityAnalysisSumAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the minimum value
    **/
    _min?: ExplainabilityAnalysisMinAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the maximum value
    **/
    _max?: ExplainabilityAnalysisMaxAggregateInputType
  }

  export type GetExplainabilityAnalysisAggregateType<T extends ExplainabilityAnalysisAggregateArgs> = {
        [P in keyof T & keyof AggregateExplainabilityAnalysis]: P extends '_count' | 'count'
      ? T[P] extends true
        ? number
        : GetScalarType<T[P], AggregateExplainabilityAnalysis[P]>
      : GetScalarType<T[P], AggregateExplainabilityAnalysis[P]>
  }




  export type ExplainabilityAnalysisGroupByArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: ExplainabilityAnalysisWhereInput
    orderBy?: ExplainabilityAnalysisOrderByWithAggregationInput | ExplainabilityAnalysisOrderByWithAggregationInput[]
    by: ExplainabilityAnalysisScalarFieldEnum[] | ExplainabilityAnalysisScalarFieldEnum
    having?: ExplainabilityAnalysisScalarWhereWithAggregatesInput
    take?: number
    skip?: number
    _count?: ExplainabilityAnalysisCountAggregateInputType | true
    _avg?: ExplainabilityAnalysisAvgAggregateInputType
    _sum?: ExplainabilityAnalysisSumAggregateInputType
    _min?: ExplainabilityAnalysisMinAggregateInputType
    _max?: ExplainabilityAnalysisMaxAggregateInputType
  }

  export type ExplainabilityAnalysisGroupByOutputType = {
    id: number
    createdAt: Date
    updatedAt: Date
    simulationId: number
    analysis: JsonValue
    _count: ExplainabilityAnalysisCountAggregateOutputType | null
    _avg: ExplainabilityAnalysisAvgAggregateOutputType | null
    _sum: ExplainabilityAnalysisSumAggregateOutputType | null
    _min: ExplainabilityAnalysisMinAggregateOutputType | null
    _max: ExplainabilityAnalysisMaxAggregateOutputType | null
  }

  type GetExplainabilityAnalysisGroupByPayload<T extends ExplainabilityAnalysisGroupByArgs> = Prisma.PrismaPromise<
    Array<
      PickEnumerable<ExplainabilityAnalysisGroupByOutputType, T['by']> &
        {
          [P in ((keyof T) & (keyof ExplainabilityAnalysisGroupByOutputType))]: P extends '_count'
            ? T[P] extends boolean
              ? number
              : GetScalarType<T[P], ExplainabilityAnalysisGroupByOutputType[P]>
            : GetScalarType<T[P], ExplainabilityAnalysisGroupByOutputType[P]>
        }
      >
    >


  export type ExplainabilityAnalysisSelect<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    simulationId?: boolean
    analysis?: boolean
    simulation?: boolean | SimulationDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["explainabilityAnalysis"]>

  export type ExplainabilityAnalysisSelectCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    simulationId?: boolean
    analysis?: boolean
    simulation?: boolean | SimulationDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["explainabilityAnalysis"]>

  export type ExplainabilityAnalysisSelectUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    simulationId?: boolean
    analysis?: boolean
    simulation?: boolean | SimulationDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["explainabilityAnalysis"]>

  export type ExplainabilityAnalysisSelectScalar = {
    id?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    simulationId?: boolean
    analysis?: boolean
  }

  export type ExplainabilityAnalysisOmit<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetOmit<"id" | "createdAt" | "updatedAt" | "simulationId" | "analysis", ExtArgs["result"]["explainabilityAnalysis"]>
  export type ExplainabilityAnalysisInclude<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    simulation?: boolean | SimulationDefaultArgs<ExtArgs>
  }
  export type ExplainabilityAnalysisIncludeCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    simulation?: boolean | SimulationDefaultArgs<ExtArgs>
  }
  export type ExplainabilityAnalysisIncludeUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    simulation?: boolean | SimulationDefaultArgs<ExtArgs>
  }

  export type $ExplainabilityAnalysisPayload<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    name: "ExplainabilityAnalysis"
    objects: {
      simulation: Prisma.$SimulationPayload<ExtArgs>
    }
    scalars: $Extensions.GetPayloadResult<{
      id: number
      createdAt: Date
      updatedAt: Date
      simulationId: number
      analysis: Prisma.JsonValue
    }, ExtArgs["result"]["explainabilityAnalysis"]>
    composites: {}
  }

  type ExplainabilityAnalysisGetPayload<S extends boolean | null | undefined | ExplainabilityAnalysisDefaultArgs> = $Result.GetResult<Prisma.$ExplainabilityAnalysisPayload, S>

  type ExplainabilityAnalysisCountArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> =
    Omit<ExplainabilityAnalysisFindManyArgs, 'select' | 'include' | 'distinct' | 'omit'> & {
      select?: ExplainabilityAnalysisCountAggregateInputType | true
    }

  export interface ExplainabilityAnalysisDelegate<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> {
    [K: symbol]: { types: Prisma.TypeMap<ExtArgs>['model']['ExplainabilityAnalysis'], meta: { name: 'ExplainabilityAnalysis' } }
    /**
     * Find zero or one ExplainabilityAnalysis that matches the filter.
     * @param {ExplainabilityAnalysisFindUniqueArgs} args - Arguments to find a ExplainabilityAnalysis
     * @example
     * // Get one ExplainabilityAnalysis
     * const explainabilityAnalysis = await prisma.explainabilityAnalysis.findUnique({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUnique<T extends ExplainabilityAnalysisFindUniqueArgs>(args: SelectSubset<T, ExplainabilityAnalysisFindUniqueArgs<ExtArgs>>): Prisma__ExplainabilityAnalysisClient<$Result.GetResult<Prisma.$ExplainabilityAnalysisPayload<ExtArgs>, T, "findUnique", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find one ExplainabilityAnalysis that matches the filter or throw an error with `error.code='P2025'`
     * if no matches were found.
     * @param {ExplainabilityAnalysisFindUniqueOrThrowArgs} args - Arguments to find a ExplainabilityAnalysis
     * @example
     * // Get one ExplainabilityAnalysis
     * const explainabilityAnalysis = await prisma.explainabilityAnalysis.findUniqueOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUniqueOrThrow<T extends ExplainabilityAnalysisFindUniqueOrThrowArgs>(args: SelectSubset<T, ExplainabilityAnalysisFindUniqueOrThrowArgs<ExtArgs>>): Prisma__ExplainabilityAnalysisClient<$Result.GetResult<Prisma.$ExplainabilityAnalysisPayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first ExplainabilityAnalysis that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {ExplainabilityAnalysisFindFirstArgs} args - Arguments to find a ExplainabilityAnalysis
     * @example
     * // Get one ExplainabilityAnalysis
     * const explainabilityAnalysis = await prisma.explainabilityAnalysis.findFirst({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirst<T extends ExplainabilityAnalysisFindFirstArgs>(args?: SelectSubset<T, ExplainabilityAnalysisFindFirstArgs<ExtArgs>>): Prisma__ExplainabilityAnalysisClient<$Result.GetResult<Prisma.$ExplainabilityAnalysisPayload<ExtArgs>, T, "findFirst", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first ExplainabilityAnalysis that matches the filter or
     * throw `PrismaKnownClientError` with `P2025` code if no matches were found.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {ExplainabilityAnalysisFindFirstOrThrowArgs} args - Arguments to find a ExplainabilityAnalysis
     * @example
     * // Get one ExplainabilityAnalysis
     * const explainabilityAnalysis = await prisma.explainabilityAnalysis.findFirstOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirstOrThrow<T extends ExplainabilityAnalysisFindFirstOrThrowArgs>(args?: SelectSubset<T, ExplainabilityAnalysisFindFirstOrThrowArgs<ExtArgs>>): Prisma__ExplainabilityAnalysisClient<$Result.GetResult<Prisma.$ExplainabilityAnalysisPayload<ExtArgs>, T, "findFirstOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find zero or more ExplainabilityAnalyses that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {ExplainabilityAnalysisFindManyArgs} args - Arguments to filter and select certain fields only.
     * @example
     * // Get all ExplainabilityAnalyses
     * const explainabilityAnalyses = await prisma.explainabilityAnalysis.findMany()
     * 
     * // Get first 10 ExplainabilityAnalyses
     * const explainabilityAnalyses = await prisma.explainabilityAnalysis.findMany({ take: 10 })
     * 
     * // Only select the `id`
     * const explainabilityAnalysisWithIdOnly = await prisma.explainabilityAnalysis.findMany({ select: { id: true } })
     * 
     */
    findMany<T extends ExplainabilityAnalysisFindManyArgs>(args?: SelectSubset<T, ExplainabilityAnalysisFindManyArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$ExplainabilityAnalysisPayload<ExtArgs>, T, "findMany", GlobalOmitOptions>>

    /**
     * Create a ExplainabilityAnalysis.
     * @param {ExplainabilityAnalysisCreateArgs} args - Arguments to create a ExplainabilityAnalysis.
     * @example
     * // Create one ExplainabilityAnalysis
     * const ExplainabilityAnalysis = await prisma.explainabilityAnalysis.create({
     *   data: {
     *     // ... data to create a ExplainabilityAnalysis
     *   }
     * })
     * 
     */
    create<T extends ExplainabilityAnalysisCreateArgs>(args: SelectSubset<T, ExplainabilityAnalysisCreateArgs<ExtArgs>>): Prisma__ExplainabilityAnalysisClient<$Result.GetResult<Prisma.$ExplainabilityAnalysisPayload<ExtArgs>, T, "create", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Create many ExplainabilityAnalyses.
     * @param {ExplainabilityAnalysisCreateManyArgs} args - Arguments to create many ExplainabilityAnalyses.
     * @example
     * // Create many ExplainabilityAnalyses
     * const explainabilityAnalysis = await prisma.explainabilityAnalysis.createMany({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     *     
     */
    createMany<T extends ExplainabilityAnalysisCreateManyArgs>(args?: SelectSubset<T, ExplainabilityAnalysisCreateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Create many ExplainabilityAnalyses and returns the data saved in the database.
     * @param {ExplainabilityAnalysisCreateManyAndReturnArgs} args - Arguments to create many ExplainabilityAnalyses.
     * @example
     * // Create many ExplainabilityAnalyses
     * const explainabilityAnalysis = await prisma.explainabilityAnalysis.createManyAndReturn({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Create many ExplainabilityAnalyses and only return the `id`
     * const explainabilityAnalysisWithIdOnly = await prisma.explainabilityAnalysis.createManyAndReturn({
     *   select: { id: true },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    createManyAndReturn<T extends ExplainabilityAnalysisCreateManyAndReturnArgs>(args?: SelectSubset<T, ExplainabilityAnalysisCreateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$ExplainabilityAnalysisPayload<ExtArgs>, T, "createManyAndReturn", GlobalOmitOptions>>

    /**
     * Delete a ExplainabilityAnalysis.
     * @param {ExplainabilityAnalysisDeleteArgs} args - Arguments to delete one ExplainabilityAnalysis.
     * @example
     * // Delete one ExplainabilityAnalysis
     * const ExplainabilityAnalysis = await prisma.explainabilityAnalysis.delete({
     *   where: {
     *     // ... filter to delete one ExplainabilityAnalysis
     *   }
     * })
     * 
     */
    delete<T extends ExplainabilityAnalysisDeleteArgs>(args: SelectSubset<T, ExplainabilityAnalysisDeleteArgs<ExtArgs>>): Prisma__ExplainabilityAnalysisClient<$Result.GetResult<Prisma.$ExplainabilityAnalysisPayload<ExtArgs>, T, "delete", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Update one ExplainabilityAnalysis.
     * @param {ExplainabilityAnalysisUpdateArgs} args - Arguments to update one ExplainabilityAnalysis.
     * @example
     * // Update one ExplainabilityAnalysis
     * const explainabilityAnalysis = await prisma.explainabilityAnalysis.update({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    update<T extends ExplainabilityAnalysisUpdateArgs>(args: SelectSubset<T, ExplainabilityAnalysisUpdateArgs<ExtArgs>>): Prisma__ExplainabilityAnalysisClient<$Result.GetResult<Prisma.$ExplainabilityAnalysisPayload<ExtArgs>, T, "update", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Delete zero or more ExplainabilityAnalyses.
     * @param {ExplainabilityAnalysisDeleteManyArgs} args - Arguments to filter ExplainabilityAnalyses to delete.
     * @example
     * // Delete a few ExplainabilityAnalyses
     * const { count } = await prisma.explainabilityAnalysis.deleteMany({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     * 
     */
    deleteMany<T extends ExplainabilityAnalysisDeleteManyArgs>(args?: SelectSubset<T, ExplainabilityAnalysisDeleteManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more ExplainabilityAnalyses.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {ExplainabilityAnalysisUpdateManyArgs} args - Arguments to update one or more rows.
     * @example
     * // Update many ExplainabilityAnalyses
     * const explainabilityAnalysis = await prisma.explainabilityAnalysis.updateMany({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    updateMany<T extends ExplainabilityAnalysisUpdateManyArgs>(args: SelectSubset<T, ExplainabilityAnalysisUpdateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more ExplainabilityAnalyses and returns the data updated in the database.
     * @param {ExplainabilityAnalysisUpdateManyAndReturnArgs} args - Arguments to update many ExplainabilityAnalyses.
     * @example
     * // Update many ExplainabilityAnalyses
     * const explainabilityAnalysis = await prisma.explainabilityAnalysis.updateManyAndReturn({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Update zero or more ExplainabilityAnalyses and only return the `id`
     * const explainabilityAnalysisWithIdOnly = await prisma.explainabilityAnalysis.updateManyAndReturn({
     *   select: { id: true },
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    updateManyAndReturn<T extends ExplainabilityAnalysisUpdateManyAndReturnArgs>(args: SelectSubset<T, ExplainabilityAnalysisUpdateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$ExplainabilityAnalysisPayload<ExtArgs>, T, "updateManyAndReturn", GlobalOmitOptions>>

    /**
     * Create or update one ExplainabilityAnalysis.
     * @param {ExplainabilityAnalysisUpsertArgs} args - Arguments to update or create a ExplainabilityAnalysis.
     * @example
     * // Update or create a ExplainabilityAnalysis
     * const explainabilityAnalysis = await prisma.explainabilityAnalysis.upsert({
     *   create: {
     *     // ... data to create a ExplainabilityAnalysis
     *   },
     *   update: {
     *     // ... in case it already exists, update
     *   },
     *   where: {
     *     // ... the filter for the ExplainabilityAnalysis we want to update
     *   }
     * })
     */
    upsert<T extends ExplainabilityAnalysisUpsertArgs>(args: SelectSubset<T, ExplainabilityAnalysisUpsertArgs<ExtArgs>>): Prisma__ExplainabilityAnalysisClient<$Result.GetResult<Prisma.$ExplainabilityAnalysisPayload<ExtArgs>, T, "upsert", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>


    /**
     * Count the number of ExplainabilityAnalyses.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {ExplainabilityAnalysisCountArgs} args - Arguments to filter ExplainabilityAnalyses to count.
     * @example
     * // Count the number of ExplainabilityAnalyses
     * const count = await prisma.explainabilityAnalysis.count({
     *   where: {
     *     // ... the filter for the ExplainabilityAnalyses we want to count
     *   }
     * })
    **/
    count<T extends ExplainabilityAnalysisCountArgs>(
      args?: Subset<T, ExplainabilityAnalysisCountArgs>,
    ): Prisma.PrismaPromise<
      T extends $Utils.Record<'select', any>
        ? T['select'] extends true
          ? number
          : GetScalarType<T['select'], ExplainabilityAnalysisCountAggregateOutputType>
        : number
    >

    /**
     * Allows you to perform aggregations operations on a ExplainabilityAnalysis.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {ExplainabilityAnalysisAggregateArgs} args - Select which aggregations you would like to apply and on what fields.
     * @example
     * // Ordered by age ascending
     * // Where email contains prisma.io
     * // Limited to the 10 users
     * const aggregations = await prisma.user.aggregate({
     *   _avg: {
     *     age: true,
     *   },
     *   where: {
     *     email: {
     *       contains: "prisma.io",
     *     },
     *   },
     *   orderBy: {
     *     age: "asc",
     *   },
     *   take: 10,
     * })
    **/
    aggregate<T extends ExplainabilityAnalysisAggregateArgs>(args: Subset<T, ExplainabilityAnalysisAggregateArgs>): Prisma.PrismaPromise<GetExplainabilityAnalysisAggregateType<T>>

    /**
     * Group by ExplainabilityAnalysis.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {ExplainabilityAnalysisGroupByArgs} args - Group by arguments.
     * @example
     * // Group by city, order by createdAt, get count
     * const result = await prisma.user.groupBy({
     *   by: ['city', 'createdAt'],
     *   orderBy: {
     *     createdAt: true
     *   },
     *   _count: {
     *     _all: true
     *   },
     * })
     * 
    **/
    groupBy<
      T extends ExplainabilityAnalysisGroupByArgs,
      HasSelectOrTake extends Or<
        Extends<'skip', Keys<T>>,
        Extends<'take', Keys<T>>
      >,
      OrderByArg extends True extends HasSelectOrTake
        ? { orderBy: ExplainabilityAnalysisGroupByArgs['orderBy'] }
        : { orderBy?: ExplainabilityAnalysisGroupByArgs['orderBy'] },
      OrderFields extends ExcludeUnderscoreKeys<Keys<MaybeTupleToUnion<T['orderBy']>>>,
      ByFields extends MaybeTupleToUnion<T['by']>,
      ByValid extends Has<ByFields, OrderFields>,
      HavingFields extends GetHavingFields<T['having']>,
      HavingValid extends Has<ByFields, HavingFields>,
      ByEmpty extends T['by'] extends never[] ? True : False,
      InputErrors extends ByEmpty extends True
      ? `Error: "by" must not be empty.`
      : HavingValid extends False
      ? {
          [P in HavingFields]: P extends ByFields
            ? never
            : P extends string
            ? `Error: Field "${P}" used in "having" needs to be provided in "by".`
            : [
                Error,
                'Field ',
                P,
                ` in "having" needs to be provided in "by"`,
              ]
        }[HavingFields]
      : 'take' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "take", you also need to provide "orderBy"'
      : 'skip' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "skip", you also need to provide "orderBy"'
      : ByValid extends True
      ? {}
      : {
          [P in OrderFields]: P extends ByFields
            ? never
            : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
        }[OrderFields]
    >(args: SubsetIntersection<T, ExplainabilityAnalysisGroupByArgs, OrderByArg> & InputErrors): {} extends InputErrors ? GetExplainabilityAnalysisGroupByPayload<T> : Prisma.PrismaPromise<InputErrors>
  /**
   * Fields of the ExplainabilityAnalysis model
   */
  readonly fields: ExplainabilityAnalysisFieldRefs;
  }

  /**
   * The delegate class that acts as a "Promise-like" for ExplainabilityAnalysis.
   * Why is this prefixed with `Prisma__`?
   * Because we want to prevent naming conflicts as mentioned in
   * https://github.com/prisma/prisma-client-js/issues/707
   */
  export interface Prisma__ExplainabilityAnalysisClient<T, Null = never, ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> extends Prisma.PrismaPromise<T> {
    readonly [Symbol.toStringTag]: "PrismaPromise"
    simulation<T extends SimulationDefaultArgs<ExtArgs> = {}>(args?: Subset<T, SimulationDefaultArgs<ExtArgs>>): Prisma__SimulationClient<$Result.GetResult<Prisma.$SimulationPayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions> | Null, Null, ExtArgs, GlobalOmitOptions>
    /**
     * Attaches callbacks for the resolution and/or rejection of the Promise.
     * @param onfulfilled The callback to execute when the Promise is resolved.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of which ever callback is executed.
     */
    then<TResult1 = T, TResult2 = never>(onfulfilled?: ((value: T) => TResult1 | PromiseLike<TResult1>) | undefined | null, onrejected?: ((reason: any) => TResult2 | PromiseLike<TResult2>) | undefined | null): $Utils.JsPromise<TResult1 | TResult2>
    /**
     * Attaches a callback for only the rejection of the Promise.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of the callback.
     */
    catch<TResult = never>(onrejected?: ((reason: any) => TResult | PromiseLike<TResult>) | undefined | null): $Utils.JsPromise<T | TResult>
    /**
     * Attaches a callback that is invoked when the Promise is settled (fulfilled or rejected). The
     * resolved value cannot be modified from the callback.
     * @param onfinally The callback to execute when the Promise is settled (fulfilled or rejected).
     * @returns A Promise for the completion of the callback.
     */
    finally(onfinally?: (() => void) | undefined | null): $Utils.JsPromise<T>
  }




  /**
   * Fields of the ExplainabilityAnalysis model
   */
  interface ExplainabilityAnalysisFieldRefs {
    readonly id: FieldRef<"ExplainabilityAnalysis", 'Int'>
    readonly createdAt: FieldRef<"ExplainabilityAnalysis", 'DateTime'>
    readonly updatedAt: FieldRef<"ExplainabilityAnalysis", 'DateTime'>
    readonly simulationId: FieldRef<"ExplainabilityAnalysis", 'Int'>
    readonly analysis: FieldRef<"ExplainabilityAnalysis", 'Json'>
  }
    

  // Custom InputTypes
  /**
   * ExplainabilityAnalysis findUnique
   */
  export type ExplainabilityAnalysisFindUniqueArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the ExplainabilityAnalysis
     */
    select?: ExplainabilityAnalysisSelect<ExtArgs> | null
    /**
     * Omit specific fields from the ExplainabilityAnalysis
     */
    omit?: ExplainabilityAnalysisOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: ExplainabilityAnalysisInclude<ExtArgs> | null
    /**
     * Filter, which ExplainabilityAnalysis to fetch.
     */
    where: ExplainabilityAnalysisWhereUniqueInput
  }

  /**
   * ExplainabilityAnalysis findUniqueOrThrow
   */
  export type ExplainabilityAnalysisFindUniqueOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the ExplainabilityAnalysis
     */
    select?: ExplainabilityAnalysisSelect<ExtArgs> | null
    /**
     * Omit specific fields from the ExplainabilityAnalysis
     */
    omit?: ExplainabilityAnalysisOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: ExplainabilityAnalysisInclude<ExtArgs> | null
    /**
     * Filter, which ExplainabilityAnalysis to fetch.
     */
    where: ExplainabilityAnalysisWhereUniqueInput
  }

  /**
   * ExplainabilityAnalysis findFirst
   */
  export type ExplainabilityAnalysisFindFirstArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the ExplainabilityAnalysis
     */
    select?: ExplainabilityAnalysisSelect<ExtArgs> | null
    /**
     * Omit specific fields from the ExplainabilityAnalysis
     */
    omit?: ExplainabilityAnalysisOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: ExplainabilityAnalysisInclude<ExtArgs> | null
    /**
     * Filter, which ExplainabilityAnalysis to fetch.
     */
    where?: ExplainabilityAnalysisWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of ExplainabilityAnalyses to fetch.
     */
    orderBy?: ExplainabilityAnalysisOrderByWithRelationInput | ExplainabilityAnalysisOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for ExplainabilityAnalyses.
     */
    cursor?: ExplainabilityAnalysisWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` ExplainabilityAnalyses from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` ExplainabilityAnalyses.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of ExplainabilityAnalyses.
     */
    distinct?: ExplainabilityAnalysisScalarFieldEnum | ExplainabilityAnalysisScalarFieldEnum[]
  }

  /**
   * ExplainabilityAnalysis findFirstOrThrow
   */
  export type ExplainabilityAnalysisFindFirstOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the ExplainabilityAnalysis
     */
    select?: ExplainabilityAnalysisSelect<ExtArgs> | null
    /**
     * Omit specific fields from the ExplainabilityAnalysis
     */
    omit?: ExplainabilityAnalysisOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: ExplainabilityAnalysisInclude<ExtArgs> | null
    /**
     * Filter, which ExplainabilityAnalysis to fetch.
     */
    where?: ExplainabilityAnalysisWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of ExplainabilityAnalyses to fetch.
     */
    orderBy?: ExplainabilityAnalysisOrderByWithRelationInput | ExplainabilityAnalysisOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for ExplainabilityAnalyses.
     */
    cursor?: ExplainabilityAnalysisWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` ExplainabilityAnalyses from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` ExplainabilityAnalyses.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of ExplainabilityAnalyses.
     */
    distinct?: ExplainabilityAnalysisScalarFieldEnum | ExplainabilityAnalysisScalarFieldEnum[]
  }

  /**
   * ExplainabilityAnalysis findMany
   */
  export type ExplainabilityAnalysisFindManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the ExplainabilityAnalysis
     */
    select?: ExplainabilityAnalysisSelect<ExtArgs> | null
    /**
     * Omit specific fields from the ExplainabilityAnalysis
     */
    omit?: ExplainabilityAnalysisOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: ExplainabilityAnalysisInclude<ExtArgs> | null
    /**
     * Filter, which ExplainabilityAnalyses to fetch.
     */
    where?: ExplainabilityAnalysisWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of ExplainabilityAnalyses to fetch.
     */
    orderBy?: ExplainabilityAnalysisOrderByWithRelationInput | ExplainabilityAnalysisOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for listing ExplainabilityAnalyses.
     */
    cursor?: ExplainabilityAnalysisWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` ExplainabilityAnalyses from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` ExplainabilityAnalyses.
     */
    skip?: number
    distinct?: ExplainabilityAnalysisScalarFieldEnum | ExplainabilityAnalysisScalarFieldEnum[]
  }

  /**
   * ExplainabilityAnalysis create
   */
  export type ExplainabilityAnalysisCreateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the ExplainabilityAnalysis
     */
    select?: ExplainabilityAnalysisSelect<ExtArgs> | null
    /**
     * Omit specific fields from the ExplainabilityAnalysis
     */
    omit?: ExplainabilityAnalysisOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: ExplainabilityAnalysisInclude<ExtArgs> | null
    /**
     * The data needed to create a ExplainabilityAnalysis.
     */
    data: XOR<ExplainabilityAnalysisCreateInput, ExplainabilityAnalysisUncheckedCreateInput>
  }

  /**
   * ExplainabilityAnalysis createMany
   */
  export type ExplainabilityAnalysisCreateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to create many ExplainabilityAnalyses.
     */
    data: ExplainabilityAnalysisCreateManyInput | ExplainabilityAnalysisCreateManyInput[]
    skipDuplicates?: boolean
  }

  /**
   * ExplainabilityAnalysis createManyAndReturn
   */
  export type ExplainabilityAnalysisCreateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the ExplainabilityAnalysis
     */
    select?: ExplainabilityAnalysisSelectCreateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the ExplainabilityAnalysis
     */
    omit?: ExplainabilityAnalysisOmit<ExtArgs> | null
    /**
     * The data used to create many ExplainabilityAnalyses.
     */
    data: ExplainabilityAnalysisCreateManyInput | ExplainabilityAnalysisCreateManyInput[]
    skipDuplicates?: boolean
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: ExplainabilityAnalysisIncludeCreateManyAndReturn<ExtArgs> | null
  }

  /**
   * ExplainabilityAnalysis update
   */
  export type ExplainabilityAnalysisUpdateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the ExplainabilityAnalysis
     */
    select?: ExplainabilityAnalysisSelect<ExtArgs> | null
    /**
     * Omit specific fields from the ExplainabilityAnalysis
     */
    omit?: ExplainabilityAnalysisOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: ExplainabilityAnalysisInclude<ExtArgs> | null
    /**
     * The data needed to update a ExplainabilityAnalysis.
     */
    data: XOR<ExplainabilityAnalysisUpdateInput, ExplainabilityAnalysisUncheckedUpdateInput>
    /**
     * Choose, which ExplainabilityAnalysis to update.
     */
    where: ExplainabilityAnalysisWhereUniqueInput
  }

  /**
   * ExplainabilityAnalysis updateMany
   */
  export type ExplainabilityAnalysisUpdateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to update ExplainabilityAnalyses.
     */
    data: XOR<ExplainabilityAnalysisUpdateManyMutationInput, ExplainabilityAnalysisUncheckedUpdateManyInput>
    /**
     * Filter which ExplainabilityAnalyses to update
     */
    where?: ExplainabilityAnalysisWhereInput
    /**
     * Limit how many ExplainabilityAnalyses to update.
     */
    limit?: number
  }

  /**
   * ExplainabilityAnalysis updateManyAndReturn
   */
  export type ExplainabilityAnalysisUpdateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the ExplainabilityAnalysis
     */
    select?: ExplainabilityAnalysisSelectUpdateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the ExplainabilityAnalysis
     */
    omit?: ExplainabilityAnalysisOmit<ExtArgs> | null
    /**
     * The data used to update ExplainabilityAnalyses.
     */
    data: XOR<ExplainabilityAnalysisUpdateManyMutationInput, ExplainabilityAnalysisUncheckedUpdateManyInput>
    /**
     * Filter which ExplainabilityAnalyses to update
     */
    where?: ExplainabilityAnalysisWhereInput
    /**
     * Limit how many ExplainabilityAnalyses to update.
     */
    limit?: number
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: ExplainabilityAnalysisIncludeUpdateManyAndReturn<ExtArgs> | null
  }

  /**
   * ExplainabilityAnalysis upsert
   */
  export type ExplainabilityAnalysisUpsertArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the ExplainabilityAnalysis
     */
    select?: ExplainabilityAnalysisSelect<ExtArgs> | null
    /**
     * Omit specific fields from the ExplainabilityAnalysis
     */
    omit?: ExplainabilityAnalysisOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: ExplainabilityAnalysisInclude<ExtArgs> | null
    /**
     * The filter to search for the ExplainabilityAnalysis to update in case it exists.
     */
    where: ExplainabilityAnalysisWhereUniqueInput
    /**
     * In case the ExplainabilityAnalysis found by the `where` argument doesn't exist, create a new ExplainabilityAnalysis with this data.
     */
    create: XOR<ExplainabilityAnalysisCreateInput, ExplainabilityAnalysisUncheckedCreateInput>
    /**
     * In case the ExplainabilityAnalysis was found with the provided `where` argument, update it with this data.
     */
    update: XOR<ExplainabilityAnalysisUpdateInput, ExplainabilityAnalysisUncheckedUpdateInput>
  }

  /**
   * ExplainabilityAnalysis delete
   */
  export type ExplainabilityAnalysisDeleteArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the ExplainabilityAnalysis
     */
    select?: ExplainabilityAnalysisSelect<ExtArgs> | null
    /**
     * Omit specific fields from the ExplainabilityAnalysis
     */
    omit?: ExplainabilityAnalysisOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: ExplainabilityAnalysisInclude<ExtArgs> | null
    /**
     * Filter which ExplainabilityAnalysis to delete.
     */
    where: ExplainabilityAnalysisWhereUniqueInput
  }

  /**
   * ExplainabilityAnalysis deleteMany
   */
  export type ExplainabilityAnalysisDeleteManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which ExplainabilityAnalyses to delete
     */
    where?: ExplainabilityAnalysisWhereInput
    /**
     * Limit how many ExplainabilityAnalyses to delete.
     */
    limit?: number
  }

  /**
   * ExplainabilityAnalysis without action
   */
  export type ExplainabilityAnalysisDefaultArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the ExplainabilityAnalysis
     */
    select?: ExplainabilityAnalysisSelect<ExtArgs> | null
    /**
     * Omit specific fields from the ExplainabilityAnalysis
     */
    omit?: ExplainabilityAnalysisOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: ExplainabilityAnalysisInclude<ExtArgs> | null
  }


  /**
   * Model ComplianceRecord
   */

  export type AggregateComplianceRecord = {
    _count: ComplianceRecordCountAggregateOutputType | null
    _avg: ComplianceRecordAvgAggregateOutputType | null
    _sum: ComplianceRecordSumAggregateOutputType | null
    _min: ComplianceRecordMinAggregateOutputType | null
    _max: ComplianceRecordMaxAggregateOutputType | null
  }

  export type ComplianceRecordAvgAggregateOutputType = {
    id: number | null
    simulationId: number | null
  }

  export type ComplianceRecordSumAggregateOutputType = {
    id: number | null
    simulationId: number | null
  }

  export type ComplianceRecordMinAggregateOutputType = {
    id: number | null
    createdAt: Date | null
    updatedAt: Date | null
    simulationId: number | null
  }

  export type ComplianceRecordMaxAggregateOutputType = {
    id: number | null
    createdAt: Date | null
    updatedAt: Date | null
    simulationId: number | null
  }

  export type ComplianceRecordCountAggregateOutputType = {
    id: number
    createdAt: number
    updatedAt: number
    simulationId: number
    record: number
    _all: number
  }


  export type ComplianceRecordAvgAggregateInputType = {
    id?: true
    simulationId?: true
  }

  export type ComplianceRecordSumAggregateInputType = {
    id?: true
    simulationId?: true
  }

  export type ComplianceRecordMinAggregateInputType = {
    id?: true
    createdAt?: true
    updatedAt?: true
    simulationId?: true
  }

  export type ComplianceRecordMaxAggregateInputType = {
    id?: true
    createdAt?: true
    updatedAt?: true
    simulationId?: true
  }

  export type ComplianceRecordCountAggregateInputType = {
    id?: true
    createdAt?: true
    updatedAt?: true
    simulationId?: true
    record?: true
    _all?: true
  }

  export type ComplianceRecordAggregateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which ComplianceRecord to aggregate.
     */
    where?: ComplianceRecordWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of ComplianceRecords to fetch.
     */
    orderBy?: ComplianceRecordOrderByWithRelationInput | ComplianceRecordOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the start position
     */
    cursor?: ComplianceRecordWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` ComplianceRecords from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` ComplianceRecords.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Count returned ComplianceRecords
    **/
    _count?: true | ComplianceRecordCountAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to average
    **/
    _avg?: ComplianceRecordAvgAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to sum
    **/
    _sum?: ComplianceRecordSumAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the minimum value
    **/
    _min?: ComplianceRecordMinAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the maximum value
    **/
    _max?: ComplianceRecordMaxAggregateInputType
  }

  export type GetComplianceRecordAggregateType<T extends ComplianceRecordAggregateArgs> = {
        [P in keyof T & keyof AggregateComplianceRecord]: P extends '_count' | 'count'
      ? T[P] extends true
        ? number
        : GetScalarType<T[P], AggregateComplianceRecord[P]>
      : GetScalarType<T[P], AggregateComplianceRecord[P]>
  }




  export type ComplianceRecordGroupByArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: ComplianceRecordWhereInput
    orderBy?: ComplianceRecordOrderByWithAggregationInput | ComplianceRecordOrderByWithAggregationInput[]
    by: ComplianceRecordScalarFieldEnum[] | ComplianceRecordScalarFieldEnum
    having?: ComplianceRecordScalarWhereWithAggregatesInput
    take?: number
    skip?: number
    _count?: ComplianceRecordCountAggregateInputType | true
    _avg?: ComplianceRecordAvgAggregateInputType
    _sum?: ComplianceRecordSumAggregateInputType
    _min?: ComplianceRecordMinAggregateInputType
    _max?: ComplianceRecordMaxAggregateInputType
  }

  export type ComplianceRecordGroupByOutputType = {
    id: number
    createdAt: Date
    updatedAt: Date
    simulationId: number
    record: JsonValue
    _count: ComplianceRecordCountAggregateOutputType | null
    _avg: ComplianceRecordAvgAggregateOutputType | null
    _sum: ComplianceRecordSumAggregateOutputType | null
    _min: ComplianceRecordMinAggregateOutputType | null
    _max: ComplianceRecordMaxAggregateOutputType | null
  }

  type GetComplianceRecordGroupByPayload<T extends ComplianceRecordGroupByArgs> = Prisma.PrismaPromise<
    Array<
      PickEnumerable<ComplianceRecordGroupByOutputType, T['by']> &
        {
          [P in ((keyof T) & (keyof ComplianceRecordGroupByOutputType))]: P extends '_count'
            ? T[P] extends boolean
              ? number
              : GetScalarType<T[P], ComplianceRecordGroupByOutputType[P]>
            : GetScalarType<T[P], ComplianceRecordGroupByOutputType[P]>
        }
      >
    >


  export type ComplianceRecordSelect<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    simulationId?: boolean
    record?: boolean
    simulation?: boolean | SimulationDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["complianceRecord"]>

  export type ComplianceRecordSelectCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    simulationId?: boolean
    record?: boolean
    simulation?: boolean | SimulationDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["complianceRecord"]>

  export type ComplianceRecordSelectUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    simulationId?: boolean
    record?: boolean
    simulation?: boolean | SimulationDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["complianceRecord"]>

  export type ComplianceRecordSelectScalar = {
    id?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    simulationId?: boolean
    record?: boolean
  }

  export type ComplianceRecordOmit<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetOmit<"id" | "createdAt" | "updatedAt" | "simulationId" | "record", ExtArgs["result"]["complianceRecord"]>
  export type ComplianceRecordInclude<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    simulation?: boolean | SimulationDefaultArgs<ExtArgs>
  }
  export type ComplianceRecordIncludeCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    simulation?: boolean | SimulationDefaultArgs<ExtArgs>
  }
  export type ComplianceRecordIncludeUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    simulation?: boolean | SimulationDefaultArgs<ExtArgs>
  }

  export type $ComplianceRecordPayload<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    name: "ComplianceRecord"
    objects: {
      simulation: Prisma.$SimulationPayload<ExtArgs>
    }
    scalars: $Extensions.GetPayloadResult<{
      id: number
      createdAt: Date
      updatedAt: Date
      simulationId: number
      record: Prisma.JsonValue
    }, ExtArgs["result"]["complianceRecord"]>
    composites: {}
  }

  type ComplianceRecordGetPayload<S extends boolean | null | undefined | ComplianceRecordDefaultArgs> = $Result.GetResult<Prisma.$ComplianceRecordPayload, S>

  type ComplianceRecordCountArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> =
    Omit<ComplianceRecordFindManyArgs, 'select' | 'include' | 'distinct' | 'omit'> & {
      select?: ComplianceRecordCountAggregateInputType | true
    }

  export interface ComplianceRecordDelegate<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> {
    [K: symbol]: { types: Prisma.TypeMap<ExtArgs>['model']['ComplianceRecord'], meta: { name: 'ComplianceRecord' } }
    /**
     * Find zero or one ComplianceRecord that matches the filter.
     * @param {ComplianceRecordFindUniqueArgs} args - Arguments to find a ComplianceRecord
     * @example
     * // Get one ComplianceRecord
     * const complianceRecord = await prisma.complianceRecord.findUnique({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUnique<T extends ComplianceRecordFindUniqueArgs>(args: SelectSubset<T, ComplianceRecordFindUniqueArgs<ExtArgs>>): Prisma__ComplianceRecordClient<$Result.GetResult<Prisma.$ComplianceRecordPayload<ExtArgs>, T, "findUnique", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find one ComplianceRecord that matches the filter or throw an error with `error.code='P2025'`
     * if no matches were found.
     * @param {ComplianceRecordFindUniqueOrThrowArgs} args - Arguments to find a ComplianceRecord
     * @example
     * // Get one ComplianceRecord
     * const complianceRecord = await prisma.complianceRecord.findUniqueOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUniqueOrThrow<T extends ComplianceRecordFindUniqueOrThrowArgs>(args: SelectSubset<T, ComplianceRecordFindUniqueOrThrowArgs<ExtArgs>>): Prisma__ComplianceRecordClient<$Result.GetResult<Prisma.$ComplianceRecordPayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first ComplianceRecord that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {ComplianceRecordFindFirstArgs} args - Arguments to find a ComplianceRecord
     * @example
     * // Get one ComplianceRecord
     * const complianceRecord = await prisma.complianceRecord.findFirst({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirst<T extends ComplianceRecordFindFirstArgs>(args?: SelectSubset<T, ComplianceRecordFindFirstArgs<ExtArgs>>): Prisma__ComplianceRecordClient<$Result.GetResult<Prisma.$ComplianceRecordPayload<ExtArgs>, T, "findFirst", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first ComplianceRecord that matches the filter or
     * throw `PrismaKnownClientError` with `P2025` code if no matches were found.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {ComplianceRecordFindFirstOrThrowArgs} args - Arguments to find a ComplianceRecord
     * @example
     * // Get one ComplianceRecord
     * const complianceRecord = await prisma.complianceRecord.findFirstOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirstOrThrow<T extends ComplianceRecordFindFirstOrThrowArgs>(args?: SelectSubset<T, ComplianceRecordFindFirstOrThrowArgs<ExtArgs>>): Prisma__ComplianceRecordClient<$Result.GetResult<Prisma.$ComplianceRecordPayload<ExtArgs>, T, "findFirstOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find zero or more ComplianceRecords that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {ComplianceRecordFindManyArgs} args - Arguments to filter and select certain fields only.
     * @example
     * // Get all ComplianceRecords
     * const complianceRecords = await prisma.complianceRecord.findMany()
     * 
     * // Get first 10 ComplianceRecords
     * const complianceRecords = await prisma.complianceRecord.findMany({ take: 10 })
     * 
     * // Only select the `id`
     * const complianceRecordWithIdOnly = await prisma.complianceRecord.findMany({ select: { id: true } })
     * 
     */
    findMany<T extends ComplianceRecordFindManyArgs>(args?: SelectSubset<T, ComplianceRecordFindManyArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$ComplianceRecordPayload<ExtArgs>, T, "findMany", GlobalOmitOptions>>

    /**
     * Create a ComplianceRecord.
     * @param {ComplianceRecordCreateArgs} args - Arguments to create a ComplianceRecord.
     * @example
     * // Create one ComplianceRecord
     * const ComplianceRecord = await prisma.complianceRecord.create({
     *   data: {
     *     // ... data to create a ComplianceRecord
     *   }
     * })
     * 
     */
    create<T extends ComplianceRecordCreateArgs>(args: SelectSubset<T, ComplianceRecordCreateArgs<ExtArgs>>): Prisma__ComplianceRecordClient<$Result.GetResult<Prisma.$ComplianceRecordPayload<ExtArgs>, T, "create", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Create many ComplianceRecords.
     * @param {ComplianceRecordCreateManyArgs} args - Arguments to create many ComplianceRecords.
     * @example
     * // Create many ComplianceRecords
     * const complianceRecord = await prisma.complianceRecord.createMany({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     *     
     */
    createMany<T extends ComplianceRecordCreateManyArgs>(args?: SelectSubset<T, ComplianceRecordCreateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Create many ComplianceRecords and returns the data saved in the database.
     * @param {ComplianceRecordCreateManyAndReturnArgs} args - Arguments to create many ComplianceRecords.
     * @example
     * // Create many ComplianceRecords
     * const complianceRecord = await prisma.complianceRecord.createManyAndReturn({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Create many ComplianceRecords and only return the `id`
     * const complianceRecordWithIdOnly = await prisma.complianceRecord.createManyAndReturn({
     *   select: { id: true },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    createManyAndReturn<T extends ComplianceRecordCreateManyAndReturnArgs>(args?: SelectSubset<T, ComplianceRecordCreateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$ComplianceRecordPayload<ExtArgs>, T, "createManyAndReturn", GlobalOmitOptions>>

    /**
     * Delete a ComplianceRecord.
     * @param {ComplianceRecordDeleteArgs} args - Arguments to delete one ComplianceRecord.
     * @example
     * // Delete one ComplianceRecord
     * const ComplianceRecord = await prisma.complianceRecord.delete({
     *   where: {
     *     // ... filter to delete one ComplianceRecord
     *   }
     * })
     * 
     */
    delete<T extends ComplianceRecordDeleteArgs>(args: SelectSubset<T, ComplianceRecordDeleteArgs<ExtArgs>>): Prisma__ComplianceRecordClient<$Result.GetResult<Prisma.$ComplianceRecordPayload<ExtArgs>, T, "delete", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Update one ComplianceRecord.
     * @param {ComplianceRecordUpdateArgs} args - Arguments to update one ComplianceRecord.
     * @example
     * // Update one ComplianceRecord
     * const complianceRecord = await prisma.complianceRecord.update({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    update<T extends ComplianceRecordUpdateArgs>(args: SelectSubset<T, ComplianceRecordUpdateArgs<ExtArgs>>): Prisma__ComplianceRecordClient<$Result.GetResult<Prisma.$ComplianceRecordPayload<ExtArgs>, T, "update", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Delete zero or more ComplianceRecords.
     * @param {ComplianceRecordDeleteManyArgs} args - Arguments to filter ComplianceRecords to delete.
     * @example
     * // Delete a few ComplianceRecords
     * const { count } = await prisma.complianceRecord.deleteMany({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     * 
     */
    deleteMany<T extends ComplianceRecordDeleteManyArgs>(args?: SelectSubset<T, ComplianceRecordDeleteManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more ComplianceRecords.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {ComplianceRecordUpdateManyArgs} args - Arguments to update one or more rows.
     * @example
     * // Update many ComplianceRecords
     * const complianceRecord = await prisma.complianceRecord.updateMany({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    updateMany<T extends ComplianceRecordUpdateManyArgs>(args: SelectSubset<T, ComplianceRecordUpdateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more ComplianceRecords and returns the data updated in the database.
     * @param {ComplianceRecordUpdateManyAndReturnArgs} args - Arguments to update many ComplianceRecords.
     * @example
     * // Update many ComplianceRecords
     * const complianceRecord = await prisma.complianceRecord.updateManyAndReturn({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Update zero or more ComplianceRecords and only return the `id`
     * const complianceRecordWithIdOnly = await prisma.complianceRecord.updateManyAndReturn({
     *   select: { id: true },
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    updateManyAndReturn<T extends ComplianceRecordUpdateManyAndReturnArgs>(args: SelectSubset<T, ComplianceRecordUpdateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$ComplianceRecordPayload<ExtArgs>, T, "updateManyAndReturn", GlobalOmitOptions>>

    /**
     * Create or update one ComplianceRecord.
     * @param {ComplianceRecordUpsertArgs} args - Arguments to update or create a ComplianceRecord.
     * @example
     * // Update or create a ComplianceRecord
     * const complianceRecord = await prisma.complianceRecord.upsert({
     *   create: {
     *     // ... data to create a ComplianceRecord
     *   },
     *   update: {
     *     // ... in case it already exists, update
     *   },
     *   where: {
     *     // ... the filter for the ComplianceRecord we want to update
     *   }
     * })
     */
    upsert<T extends ComplianceRecordUpsertArgs>(args: SelectSubset<T, ComplianceRecordUpsertArgs<ExtArgs>>): Prisma__ComplianceRecordClient<$Result.GetResult<Prisma.$ComplianceRecordPayload<ExtArgs>, T, "upsert", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>


    /**
     * Count the number of ComplianceRecords.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {ComplianceRecordCountArgs} args - Arguments to filter ComplianceRecords to count.
     * @example
     * // Count the number of ComplianceRecords
     * const count = await prisma.complianceRecord.count({
     *   where: {
     *     // ... the filter for the ComplianceRecords we want to count
     *   }
     * })
    **/
    count<T extends ComplianceRecordCountArgs>(
      args?: Subset<T, ComplianceRecordCountArgs>,
    ): Prisma.PrismaPromise<
      T extends $Utils.Record<'select', any>
        ? T['select'] extends true
          ? number
          : GetScalarType<T['select'], ComplianceRecordCountAggregateOutputType>
        : number
    >

    /**
     * Allows you to perform aggregations operations on a ComplianceRecord.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {ComplianceRecordAggregateArgs} args - Select which aggregations you would like to apply and on what fields.
     * @example
     * // Ordered by age ascending
     * // Where email contains prisma.io
     * // Limited to the 10 users
     * const aggregations = await prisma.user.aggregate({
     *   _avg: {
     *     age: true,
     *   },
     *   where: {
     *     email: {
     *       contains: "prisma.io",
     *     },
     *   },
     *   orderBy: {
     *     age: "asc",
     *   },
     *   take: 10,
     * })
    **/
    aggregate<T extends ComplianceRecordAggregateArgs>(args: Subset<T, ComplianceRecordAggregateArgs>): Prisma.PrismaPromise<GetComplianceRecordAggregateType<T>>

    /**
     * Group by ComplianceRecord.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {ComplianceRecordGroupByArgs} args - Group by arguments.
     * @example
     * // Group by city, order by createdAt, get count
     * const result = await prisma.user.groupBy({
     *   by: ['city', 'createdAt'],
     *   orderBy: {
     *     createdAt: true
     *   },
     *   _count: {
     *     _all: true
     *   },
     * })
     * 
    **/
    groupBy<
      T extends ComplianceRecordGroupByArgs,
      HasSelectOrTake extends Or<
        Extends<'skip', Keys<T>>,
        Extends<'take', Keys<T>>
      >,
      OrderByArg extends True extends HasSelectOrTake
        ? { orderBy: ComplianceRecordGroupByArgs['orderBy'] }
        : { orderBy?: ComplianceRecordGroupByArgs['orderBy'] },
      OrderFields extends ExcludeUnderscoreKeys<Keys<MaybeTupleToUnion<T['orderBy']>>>,
      ByFields extends MaybeTupleToUnion<T['by']>,
      ByValid extends Has<ByFields, OrderFields>,
      HavingFields extends GetHavingFields<T['having']>,
      HavingValid extends Has<ByFields, HavingFields>,
      ByEmpty extends T['by'] extends never[] ? True : False,
      InputErrors extends ByEmpty extends True
      ? `Error: "by" must not be empty.`
      : HavingValid extends False
      ? {
          [P in HavingFields]: P extends ByFields
            ? never
            : P extends string
            ? `Error: Field "${P}" used in "having" needs to be provided in "by".`
            : [
                Error,
                'Field ',
                P,
                ` in "having" needs to be provided in "by"`,
              ]
        }[HavingFields]
      : 'take' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "take", you also need to provide "orderBy"'
      : 'skip' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "skip", you also need to provide "orderBy"'
      : ByValid extends True
      ? {}
      : {
          [P in OrderFields]: P extends ByFields
            ? never
            : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
        }[OrderFields]
    >(args: SubsetIntersection<T, ComplianceRecordGroupByArgs, OrderByArg> & InputErrors): {} extends InputErrors ? GetComplianceRecordGroupByPayload<T> : Prisma.PrismaPromise<InputErrors>
  /**
   * Fields of the ComplianceRecord model
   */
  readonly fields: ComplianceRecordFieldRefs;
  }

  /**
   * The delegate class that acts as a "Promise-like" for ComplianceRecord.
   * Why is this prefixed with `Prisma__`?
   * Because we want to prevent naming conflicts as mentioned in
   * https://github.com/prisma/prisma-client-js/issues/707
   */
  export interface Prisma__ComplianceRecordClient<T, Null = never, ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> extends Prisma.PrismaPromise<T> {
    readonly [Symbol.toStringTag]: "PrismaPromise"
    simulation<T extends SimulationDefaultArgs<ExtArgs> = {}>(args?: Subset<T, SimulationDefaultArgs<ExtArgs>>): Prisma__SimulationClient<$Result.GetResult<Prisma.$SimulationPayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions> | Null, Null, ExtArgs, GlobalOmitOptions>
    /**
     * Attaches callbacks for the resolution and/or rejection of the Promise.
     * @param onfulfilled The callback to execute when the Promise is resolved.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of which ever callback is executed.
     */
    then<TResult1 = T, TResult2 = never>(onfulfilled?: ((value: T) => TResult1 | PromiseLike<TResult1>) | undefined | null, onrejected?: ((reason: any) => TResult2 | PromiseLike<TResult2>) | undefined | null): $Utils.JsPromise<TResult1 | TResult2>
    /**
     * Attaches a callback for only the rejection of the Promise.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of the callback.
     */
    catch<TResult = never>(onrejected?: ((reason: any) => TResult | PromiseLike<TResult>) | undefined | null): $Utils.JsPromise<T | TResult>
    /**
     * Attaches a callback that is invoked when the Promise is settled (fulfilled or rejected). The
     * resolved value cannot be modified from the callback.
     * @param onfinally The callback to execute when the Promise is settled (fulfilled or rejected).
     * @returns A Promise for the completion of the callback.
     */
    finally(onfinally?: (() => void) | undefined | null): $Utils.JsPromise<T>
  }




  /**
   * Fields of the ComplianceRecord model
   */
  interface ComplianceRecordFieldRefs {
    readonly id: FieldRef<"ComplianceRecord", 'Int'>
    readonly createdAt: FieldRef<"ComplianceRecord", 'DateTime'>
    readonly updatedAt: FieldRef<"ComplianceRecord", 'DateTime'>
    readonly simulationId: FieldRef<"ComplianceRecord", 'Int'>
    readonly record: FieldRef<"ComplianceRecord", 'Json'>
  }
    

  // Custom InputTypes
  /**
   * ComplianceRecord findUnique
   */
  export type ComplianceRecordFindUniqueArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the ComplianceRecord
     */
    select?: ComplianceRecordSelect<ExtArgs> | null
    /**
     * Omit specific fields from the ComplianceRecord
     */
    omit?: ComplianceRecordOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: ComplianceRecordInclude<ExtArgs> | null
    /**
     * Filter, which ComplianceRecord to fetch.
     */
    where: ComplianceRecordWhereUniqueInput
  }

  /**
   * ComplianceRecord findUniqueOrThrow
   */
  export type ComplianceRecordFindUniqueOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the ComplianceRecord
     */
    select?: ComplianceRecordSelect<ExtArgs> | null
    /**
     * Omit specific fields from the ComplianceRecord
     */
    omit?: ComplianceRecordOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: ComplianceRecordInclude<ExtArgs> | null
    /**
     * Filter, which ComplianceRecord to fetch.
     */
    where: ComplianceRecordWhereUniqueInput
  }

  /**
   * ComplianceRecord findFirst
   */
  export type ComplianceRecordFindFirstArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the ComplianceRecord
     */
    select?: ComplianceRecordSelect<ExtArgs> | null
    /**
     * Omit specific fields from the ComplianceRecord
     */
    omit?: ComplianceRecordOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: ComplianceRecordInclude<ExtArgs> | null
    /**
     * Filter, which ComplianceRecord to fetch.
     */
    where?: ComplianceRecordWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of ComplianceRecords to fetch.
     */
    orderBy?: ComplianceRecordOrderByWithRelationInput | ComplianceRecordOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for ComplianceRecords.
     */
    cursor?: ComplianceRecordWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` ComplianceRecords from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` ComplianceRecords.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of ComplianceRecords.
     */
    distinct?: ComplianceRecordScalarFieldEnum | ComplianceRecordScalarFieldEnum[]
  }

  /**
   * ComplianceRecord findFirstOrThrow
   */
  export type ComplianceRecordFindFirstOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the ComplianceRecord
     */
    select?: ComplianceRecordSelect<ExtArgs> | null
    /**
     * Omit specific fields from the ComplianceRecord
     */
    omit?: ComplianceRecordOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: ComplianceRecordInclude<ExtArgs> | null
    /**
     * Filter, which ComplianceRecord to fetch.
     */
    where?: ComplianceRecordWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of ComplianceRecords to fetch.
     */
    orderBy?: ComplianceRecordOrderByWithRelationInput | ComplianceRecordOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for ComplianceRecords.
     */
    cursor?: ComplianceRecordWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` ComplianceRecords from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` ComplianceRecords.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of ComplianceRecords.
     */
    distinct?: ComplianceRecordScalarFieldEnum | ComplianceRecordScalarFieldEnum[]
  }

  /**
   * ComplianceRecord findMany
   */
  export type ComplianceRecordFindManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the ComplianceRecord
     */
    select?: ComplianceRecordSelect<ExtArgs> | null
    /**
     * Omit specific fields from the ComplianceRecord
     */
    omit?: ComplianceRecordOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: ComplianceRecordInclude<ExtArgs> | null
    /**
     * Filter, which ComplianceRecords to fetch.
     */
    where?: ComplianceRecordWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of ComplianceRecords to fetch.
     */
    orderBy?: ComplianceRecordOrderByWithRelationInput | ComplianceRecordOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for listing ComplianceRecords.
     */
    cursor?: ComplianceRecordWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` ComplianceRecords from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` ComplianceRecords.
     */
    skip?: number
    distinct?: ComplianceRecordScalarFieldEnum | ComplianceRecordScalarFieldEnum[]
  }

  /**
   * ComplianceRecord create
   */
  export type ComplianceRecordCreateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the ComplianceRecord
     */
    select?: ComplianceRecordSelect<ExtArgs> | null
    /**
     * Omit specific fields from the ComplianceRecord
     */
    omit?: ComplianceRecordOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: ComplianceRecordInclude<ExtArgs> | null
    /**
     * The data needed to create a ComplianceRecord.
     */
    data: XOR<ComplianceRecordCreateInput, ComplianceRecordUncheckedCreateInput>
  }

  /**
   * ComplianceRecord createMany
   */
  export type ComplianceRecordCreateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to create many ComplianceRecords.
     */
    data: ComplianceRecordCreateManyInput | ComplianceRecordCreateManyInput[]
    skipDuplicates?: boolean
  }

  /**
   * ComplianceRecord createManyAndReturn
   */
  export type ComplianceRecordCreateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the ComplianceRecord
     */
    select?: ComplianceRecordSelectCreateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the ComplianceRecord
     */
    omit?: ComplianceRecordOmit<ExtArgs> | null
    /**
     * The data used to create many ComplianceRecords.
     */
    data: ComplianceRecordCreateManyInput | ComplianceRecordCreateManyInput[]
    skipDuplicates?: boolean
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: ComplianceRecordIncludeCreateManyAndReturn<ExtArgs> | null
  }

  /**
   * ComplianceRecord update
   */
  export type ComplianceRecordUpdateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the ComplianceRecord
     */
    select?: ComplianceRecordSelect<ExtArgs> | null
    /**
     * Omit specific fields from the ComplianceRecord
     */
    omit?: ComplianceRecordOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: ComplianceRecordInclude<ExtArgs> | null
    /**
     * The data needed to update a ComplianceRecord.
     */
    data: XOR<ComplianceRecordUpdateInput, ComplianceRecordUncheckedUpdateInput>
    /**
     * Choose, which ComplianceRecord to update.
     */
    where: ComplianceRecordWhereUniqueInput
  }

  /**
   * ComplianceRecord updateMany
   */
  export type ComplianceRecordUpdateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to update ComplianceRecords.
     */
    data: XOR<ComplianceRecordUpdateManyMutationInput, ComplianceRecordUncheckedUpdateManyInput>
    /**
     * Filter which ComplianceRecords to update
     */
    where?: ComplianceRecordWhereInput
    /**
     * Limit how many ComplianceRecords to update.
     */
    limit?: number
  }

  /**
   * ComplianceRecord updateManyAndReturn
   */
  export type ComplianceRecordUpdateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the ComplianceRecord
     */
    select?: ComplianceRecordSelectUpdateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the ComplianceRecord
     */
    omit?: ComplianceRecordOmit<ExtArgs> | null
    /**
     * The data used to update ComplianceRecords.
     */
    data: XOR<ComplianceRecordUpdateManyMutationInput, ComplianceRecordUncheckedUpdateManyInput>
    /**
     * Filter which ComplianceRecords to update
     */
    where?: ComplianceRecordWhereInput
    /**
     * Limit how many ComplianceRecords to update.
     */
    limit?: number
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: ComplianceRecordIncludeUpdateManyAndReturn<ExtArgs> | null
  }

  /**
   * ComplianceRecord upsert
   */
  export type ComplianceRecordUpsertArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the ComplianceRecord
     */
    select?: ComplianceRecordSelect<ExtArgs> | null
    /**
     * Omit specific fields from the ComplianceRecord
     */
    omit?: ComplianceRecordOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: ComplianceRecordInclude<ExtArgs> | null
    /**
     * The filter to search for the ComplianceRecord to update in case it exists.
     */
    where: ComplianceRecordWhereUniqueInput
    /**
     * In case the ComplianceRecord found by the `where` argument doesn't exist, create a new ComplianceRecord with this data.
     */
    create: XOR<ComplianceRecordCreateInput, ComplianceRecordUncheckedCreateInput>
    /**
     * In case the ComplianceRecord was found with the provided `where` argument, update it with this data.
     */
    update: XOR<ComplianceRecordUpdateInput, ComplianceRecordUncheckedUpdateInput>
  }

  /**
   * ComplianceRecord delete
   */
  export type ComplianceRecordDeleteArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the ComplianceRecord
     */
    select?: ComplianceRecordSelect<ExtArgs> | null
    /**
     * Omit specific fields from the ComplianceRecord
     */
    omit?: ComplianceRecordOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: ComplianceRecordInclude<ExtArgs> | null
    /**
     * Filter which ComplianceRecord to delete.
     */
    where: ComplianceRecordWhereUniqueInput
  }

  /**
   * ComplianceRecord deleteMany
   */
  export type ComplianceRecordDeleteManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which ComplianceRecords to delete
     */
    where?: ComplianceRecordWhereInput
    /**
     * Limit how many ComplianceRecords to delete.
     */
    limit?: number
  }

  /**
   * ComplianceRecord without action
   */
  export type ComplianceRecordDefaultArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the ComplianceRecord
     */
    select?: ComplianceRecordSelect<ExtArgs> | null
    /**
     * Omit specific fields from the ComplianceRecord
     */
    omit?: ComplianceRecordOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: ComplianceRecordInclude<ExtArgs> | null
  }


  /**
   * Model RiskAssessment
   */

  export type AggregateRiskAssessment = {
    _count: RiskAssessmentCountAggregateOutputType | null
    _avg: RiskAssessmentAvgAggregateOutputType | null
    _sum: RiskAssessmentSumAggregateOutputType | null
    _min: RiskAssessmentMinAggregateOutputType | null
    _max: RiskAssessmentMaxAggregateOutputType | null
  }

  export type RiskAssessmentAvgAggregateOutputType = {
    id: number | null
    simulationId: number | null
  }

  export type RiskAssessmentSumAggregateOutputType = {
    id: number | null
    simulationId: number | null
  }

  export type RiskAssessmentMinAggregateOutputType = {
    id: number | null
    createdAt: Date | null
    updatedAt: Date | null
    simulationId: number | null
  }

  export type RiskAssessmentMaxAggregateOutputType = {
    id: number | null
    createdAt: Date | null
    updatedAt: Date | null
    simulationId: number | null
  }

  export type RiskAssessmentCountAggregateOutputType = {
    id: number
    createdAt: number
    updatedAt: number
    simulationId: number
    assessment: number
    _all: number
  }


  export type RiskAssessmentAvgAggregateInputType = {
    id?: true
    simulationId?: true
  }

  export type RiskAssessmentSumAggregateInputType = {
    id?: true
    simulationId?: true
  }

  export type RiskAssessmentMinAggregateInputType = {
    id?: true
    createdAt?: true
    updatedAt?: true
    simulationId?: true
  }

  export type RiskAssessmentMaxAggregateInputType = {
    id?: true
    createdAt?: true
    updatedAt?: true
    simulationId?: true
  }

  export type RiskAssessmentCountAggregateInputType = {
    id?: true
    createdAt?: true
    updatedAt?: true
    simulationId?: true
    assessment?: true
    _all?: true
  }

  export type RiskAssessmentAggregateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which RiskAssessment to aggregate.
     */
    where?: RiskAssessmentWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of RiskAssessments to fetch.
     */
    orderBy?: RiskAssessmentOrderByWithRelationInput | RiskAssessmentOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the start position
     */
    cursor?: RiskAssessmentWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` RiskAssessments from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` RiskAssessments.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Count returned RiskAssessments
    **/
    _count?: true | RiskAssessmentCountAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to average
    **/
    _avg?: RiskAssessmentAvgAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to sum
    **/
    _sum?: RiskAssessmentSumAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the minimum value
    **/
    _min?: RiskAssessmentMinAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the maximum value
    **/
    _max?: RiskAssessmentMaxAggregateInputType
  }

  export type GetRiskAssessmentAggregateType<T extends RiskAssessmentAggregateArgs> = {
        [P in keyof T & keyof AggregateRiskAssessment]: P extends '_count' | 'count'
      ? T[P] extends true
        ? number
        : GetScalarType<T[P], AggregateRiskAssessment[P]>
      : GetScalarType<T[P], AggregateRiskAssessment[P]>
  }




  export type RiskAssessmentGroupByArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: RiskAssessmentWhereInput
    orderBy?: RiskAssessmentOrderByWithAggregationInput | RiskAssessmentOrderByWithAggregationInput[]
    by: RiskAssessmentScalarFieldEnum[] | RiskAssessmentScalarFieldEnum
    having?: RiskAssessmentScalarWhereWithAggregatesInput
    take?: number
    skip?: number
    _count?: RiskAssessmentCountAggregateInputType | true
    _avg?: RiskAssessmentAvgAggregateInputType
    _sum?: RiskAssessmentSumAggregateInputType
    _min?: RiskAssessmentMinAggregateInputType
    _max?: RiskAssessmentMaxAggregateInputType
  }

  export type RiskAssessmentGroupByOutputType = {
    id: number
    createdAt: Date
    updatedAt: Date
    simulationId: number
    assessment: JsonValue
    _count: RiskAssessmentCountAggregateOutputType | null
    _avg: RiskAssessmentAvgAggregateOutputType | null
    _sum: RiskAssessmentSumAggregateOutputType | null
    _min: RiskAssessmentMinAggregateOutputType | null
    _max: RiskAssessmentMaxAggregateOutputType | null
  }

  type GetRiskAssessmentGroupByPayload<T extends RiskAssessmentGroupByArgs> = Prisma.PrismaPromise<
    Array<
      PickEnumerable<RiskAssessmentGroupByOutputType, T['by']> &
        {
          [P in ((keyof T) & (keyof RiskAssessmentGroupByOutputType))]: P extends '_count'
            ? T[P] extends boolean
              ? number
              : GetScalarType<T[P], RiskAssessmentGroupByOutputType[P]>
            : GetScalarType<T[P], RiskAssessmentGroupByOutputType[P]>
        }
      >
    >


  export type RiskAssessmentSelect<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    simulationId?: boolean
    assessment?: boolean
    simulation?: boolean | SimulationDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["riskAssessment"]>

  export type RiskAssessmentSelectCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    simulationId?: boolean
    assessment?: boolean
    simulation?: boolean | SimulationDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["riskAssessment"]>

  export type RiskAssessmentSelectUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    simulationId?: boolean
    assessment?: boolean
    simulation?: boolean | SimulationDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["riskAssessment"]>

  export type RiskAssessmentSelectScalar = {
    id?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    simulationId?: boolean
    assessment?: boolean
  }

  export type RiskAssessmentOmit<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetOmit<"id" | "createdAt" | "updatedAt" | "simulationId" | "assessment", ExtArgs["result"]["riskAssessment"]>
  export type RiskAssessmentInclude<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    simulation?: boolean | SimulationDefaultArgs<ExtArgs>
  }
  export type RiskAssessmentIncludeCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    simulation?: boolean | SimulationDefaultArgs<ExtArgs>
  }
  export type RiskAssessmentIncludeUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    simulation?: boolean | SimulationDefaultArgs<ExtArgs>
  }

  export type $RiskAssessmentPayload<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    name: "RiskAssessment"
    objects: {
      simulation: Prisma.$SimulationPayload<ExtArgs>
    }
    scalars: $Extensions.GetPayloadResult<{
      id: number
      createdAt: Date
      updatedAt: Date
      simulationId: number
      assessment: Prisma.JsonValue
    }, ExtArgs["result"]["riskAssessment"]>
    composites: {}
  }

  type RiskAssessmentGetPayload<S extends boolean | null | undefined | RiskAssessmentDefaultArgs> = $Result.GetResult<Prisma.$RiskAssessmentPayload, S>

  type RiskAssessmentCountArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> =
    Omit<RiskAssessmentFindManyArgs, 'select' | 'include' | 'distinct' | 'omit'> & {
      select?: RiskAssessmentCountAggregateInputType | true
    }

  export interface RiskAssessmentDelegate<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> {
    [K: symbol]: { types: Prisma.TypeMap<ExtArgs>['model']['RiskAssessment'], meta: { name: 'RiskAssessment' } }
    /**
     * Find zero or one RiskAssessment that matches the filter.
     * @param {RiskAssessmentFindUniqueArgs} args - Arguments to find a RiskAssessment
     * @example
     * // Get one RiskAssessment
     * const riskAssessment = await prisma.riskAssessment.findUnique({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUnique<T extends RiskAssessmentFindUniqueArgs>(args: SelectSubset<T, RiskAssessmentFindUniqueArgs<ExtArgs>>): Prisma__RiskAssessmentClient<$Result.GetResult<Prisma.$RiskAssessmentPayload<ExtArgs>, T, "findUnique", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find one RiskAssessment that matches the filter or throw an error with `error.code='P2025'`
     * if no matches were found.
     * @param {RiskAssessmentFindUniqueOrThrowArgs} args - Arguments to find a RiskAssessment
     * @example
     * // Get one RiskAssessment
     * const riskAssessment = await prisma.riskAssessment.findUniqueOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUniqueOrThrow<T extends RiskAssessmentFindUniqueOrThrowArgs>(args: SelectSubset<T, RiskAssessmentFindUniqueOrThrowArgs<ExtArgs>>): Prisma__RiskAssessmentClient<$Result.GetResult<Prisma.$RiskAssessmentPayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first RiskAssessment that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {RiskAssessmentFindFirstArgs} args - Arguments to find a RiskAssessment
     * @example
     * // Get one RiskAssessment
     * const riskAssessment = await prisma.riskAssessment.findFirst({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirst<T extends RiskAssessmentFindFirstArgs>(args?: SelectSubset<T, RiskAssessmentFindFirstArgs<ExtArgs>>): Prisma__RiskAssessmentClient<$Result.GetResult<Prisma.$RiskAssessmentPayload<ExtArgs>, T, "findFirst", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first RiskAssessment that matches the filter or
     * throw `PrismaKnownClientError` with `P2025` code if no matches were found.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {RiskAssessmentFindFirstOrThrowArgs} args - Arguments to find a RiskAssessment
     * @example
     * // Get one RiskAssessment
     * const riskAssessment = await prisma.riskAssessment.findFirstOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirstOrThrow<T extends RiskAssessmentFindFirstOrThrowArgs>(args?: SelectSubset<T, RiskAssessmentFindFirstOrThrowArgs<ExtArgs>>): Prisma__RiskAssessmentClient<$Result.GetResult<Prisma.$RiskAssessmentPayload<ExtArgs>, T, "findFirstOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find zero or more RiskAssessments that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {RiskAssessmentFindManyArgs} args - Arguments to filter and select certain fields only.
     * @example
     * // Get all RiskAssessments
     * const riskAssessments = await prisma.riskAssessment.findMany()
     * 
     * // Get first 10 RiskAssessments
     * const riskAssessments = await prisma.riskAssessment.findMany({ take: 10 })
     * 
     * // Only select the `id`
     * const riskAssessmentWithIdOnly = await prisma.riskAssessment.findMany({ select: { id: true } })
     * 
     */
    findMany<T extends RiskAssessmentFindManyArgs>(args?: SelectSubset<T, RiskAssessmentFindManyArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$RiskAssessmentPayload<ExtArgs>, T, "findMany", GlobalOmitOptions>>

    /**
     * Create a RiskAssessment.
     * @param {RiskAssessmentCreateArgs} args - Arguments to create a RiskAssessment.
     * @example
     * // Create one RiskAssessment
     * const RiskAssessment = await prisma.riskAssessment.create({
     *   data: {
     *     // ... data to create a RiskAssessment
     *   }
     * })
     * 
     */
    create<T extends RiskAssessmentCreateArgs>(args: SelectSubset<T, RiskAssessmentCreateArgs<ExtArgs>>): Prisma__RiskAssessmentClient<$Result.GetResult<Prisma.$RiskAssessmentPayload<ExtArgs>, T, "create", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Create many RiskAssessments.
     * @param {RiskAssessmentCreateManyArgs} args - Arguments to create many RiskAssessments.
     * @example
     * // Create many RiskAssessments
     * const riskAssessment = await prisma.riskAssessment.createMany({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     *     
     */
    createMany<T extends RiskAssessmentCreateManyArgs>(args?: SelectSubset<T, RiskAssessmentCreateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Create many RiskAssessments and returns the data saved in the database.
     * @param {RiskAssessmentCreateManyAndReturnArgs} args - Arguments to create many RiskAssessments.
     * @example
     * // Create many RiskAssessments
     * const riskAssessment = await prisma.riskAssessment.createManyAndReturn({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Create many RiskAssessments and only return the `id`
     * const riskAssessmentWithIdOnly = await prisma.riskAssessment.createManyAndReturn({
     *   select: { id: true },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    createManyAndReturn<T extends RiskAssessmentCreateManyAndReturnArgs>(args?: SelectSubset<T, RiskAssessmentCreateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$RiskAssessmentPayload<ExtArgs>, T, "createManyAndReturn", GlobalOmitOptions>>

    /**
     * Delete a RiskAssessment.
     * @param {RiskAssessmentDeleteArgs} args - Arguments to delete one RiskAssessment.
     * @example
     * // Delete one RiskAssessment
     * const RiskAssessment = await prisma.riskAssessment.delete({
     *   where: {
     *     // ... filter to delete one RiskAssessment
     *   }
     * })
     * 
     */
    delete<T extends RiskAssessmentDeleteArgs>(args: SelectSubset<T, RiskAssessmentDeleteArgs<ExtArgs>>): Prisma__RiskAssessmentClient<$Result.GetResult<Prisma.$RiskAssessmentPayload<ExtArgs>, T, "delete", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Update one RiskAssessment.
     * @param {RiskAssessmentUpdateArgs} args - Arguments to update one RiskAssessment.
     * @example
     * // Update one RiskAssessment
     * const riskAssessment = await prisma.riskAssessment.update({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    update<T extends RiskAssessmentUpdateArgs>(args: SelectSubset<T, RiskAssessmentUpdateArgs<ExtArgs>>): Prisma__RiskAssessmentClient<$Result.GetResult<Prisma.$RiskAssessmentPayload<ExtArgs>, T, "update", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Delete zero or more RiskAssessments.
     * @param {RiskAssessmentDeleteManyArgs} args - Arguments to filter RiskAssessments to delete.
     * @example
     * // Delete a few RiskAssessments
     * const { count } = await prisma.riskAssessment.deleteMany({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     * 
     */
    deleteMany<T extends RiskAssessmentDeleteManyArgs>(args?: SelectSubset<T, RiskAssessmentDeleteManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more RiskAssessments.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {RiskAssessmentUpdateManyArgs} args - Arguments to update one or more rows.
     * @example
     * // Update many RiskAssessments
     * const riskAssessment = await prisma.riskAssessment.updateMany({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    updateMany<T extends RiskAssessmentUpdateManyArgs>(args: SelectSubset<T, RiskAssessmentUpdateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more RiskAssessments and returns the data updated in the database.
     * @param {RiskAssessmentUpdateManyAndReturnArgs} args - Arguments to update many RiskAssessments.
     * @example
     * // Update many RiskAssessments
     * const riskAssessment = await prisma.riskAssessment.updateManyAndReturn({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Update zero or more RiskAssessments and only return the `id`
     * const riskAssessmentWithIdOnly = await prisma.riskAssessment.updateManyAndReturn({
     *   select: { id: true },
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    updateManyAndReturn<T extends RiskAssessmentUpdateManyAndReturnArgs>(args: SelectSubset<T, RiskAssessmentUpdateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$RiskAssessmentPayload<ExtArgs>, T, "updateManyAndReturn", GlobalOmitOptions>>

    /**
     * Create or update one RiskAssessment.
     * @param {RiskAssessmentUpsertArgs} args - Arguments to update or create a RiskAssessment.
     * @example
     * // Update or create a RiskAssessment
     * const riskAssessment = await prisma.riskAssessment.upsert({
     *   create: {
     *     // ... data to create a RiskAssessment
     *   },
     *   update: {
     *     // ... in case it already exists, update
     *   },
     *   where: {
     *     // ... the filter for the RiskAssessment we want to update
     *   }
     * })
     */
    upsert<T extends RiskAssessmentUpsertArgs>(args: SelectSubset<T, RiskAssessmentUpsertArgs<ExtArgs>>): Prisma__RiskAssessmentClient<$Result.GetResult<Prisma.$RiskAssessmentPayload<ExtArgs>, T, "upsert", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>


    /**
     * Count the number of RiskAssessments.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {RiskAssessmentCountArgs} args - Arguments to filter RiskAssessments to count.
     * @example
     * // Count the number of RiskAssessments
     * const count = await prisma.riskAssessment.count({
     *   where: {
     *     // ... the filter for the RiskAssessments we want to count
     *   }
     * })
    **/
    count<T extends RiskAssessmentCountArgs>(
      args?: Subset<T, RiskAssessmentCountArgs>,
    ): Prisma.PrismaPromise<
      T extends $Utils.Record<'select', any>
        ? T['select'] extends true
          ? number
          : GetScalarType<T['select'], RiskAssessmentCountAggregateOutputType>
        : number
    >

    /**
     * Allows you to perform aggregations operations on a RiskAssessment.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {RiskAssessmentAggregateArgs} args - Select which aggregations you would like to apply and on what fields.
     * @example
     * // Ordered by age ascending
     * // Where email contains prisma.io
     * // Limited to the 10 users
     * const aggregations = await prisma.user.aggregate({
     *   _avg: {
     *     age: true,
     *   },
     *   where: {
     *     email: {
     *       contains: "prisma.io",
     *     },
     *   },
     *   orderBy: {
     *     age: "asc",
     *   },
     *   take: 10,
     * })
    **/
    aggregate<T extends RiskAssessmentAggregateArgs>(args: Subset<T, RiskAssessmentAggregateArgs>): Prisma.PrismaPromise<GetRiskAssessmentAggregateType<T>>

    /**
     * Group by RiskAssessment.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {RiskAssessmentGroupByArgs} args - Group by arguments.
     * @example
     * // Group by city, order by createdAt, get count
     * const result = await prisma.user.groupBy({
     *   by: ['city', 'createdAt'],
     *   orderBy: {
     *     createdAt: true
     *   },
     *   _count: {
     *     _all: true
     *   },
     * })
     * 
    **/
    groupBy<
      T extends RiskAssessmentGroupByArgs,
      HasSelectOrTake extends Or<
        Extends<'skip', Keys<T>>,
        Extends<'take', Keys<T>>
      >,
      OrderByArg extends True extends HasSelectOrTake
        ? { orderBy: RiskAssessmentGroupByArgs['orderBy'] }
        : { orderBy?: RiskAssessmentGroupByArgs['orderBy'] },
      OrderFields extends ExcludeUnderscoreKeys<Keys<MaybeTupleToUnion<T['orderBy']>>>,
      ByFields extends MaybeTupleToUnion<T['by']>,
      ByValid extends Has<ByFields, OrderFields>,
      HavingFields extends GetHavingFields<T['having']>,
      HavingValid extends Has<ByFields, HavingFields>,
      ByEmpty extends T['by'] extends never[] ? True : False,
      InputErrors extends ByEmpty extends True
      ? `Error: "by" must not be empty.`
      : HavingValid extends False
      ? {
          [P in HavingFields]: P extends ByFields
            ? never
            : P extends string
            ? `Error: Field "${P}" used in "having" needs to be provided in "by".`
            : [
                Error,
                'Field ',
                P,
                ` in "having" needs to be provided in "by"`,
              ]
        }[HavingFields]
      : 'take' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "take", you also need to provide "orderBy"'
      : 'skip' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "skip", you also need to provide "orderBy"'
      : ByValid extends True
      ? {}
      : {
          [P in OrderFields]: P extends ByFields
            ? never
            : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
        }[OrderFields]
    >(args: SubsetIntersection<T, RiskAssessmentGroupByArgs, OrderByArg> & InputErrors): {} extends InputErrors ? GetRiskAssessmentGroupByPayload<T> : Prisma.PrismaPromise<InputErrors>
  /**
   * Fields of the RiskAssessment model
   */
  readonly fields: RiskAssessmentFieldRefs;
  }

  /**
   * The delegate class that acts as a "Promise-like" for RiskAssessment.
   * Why is this prefixed with `Prisma__`?
   * Because we want to prevent naming conflicts as mentioned in
   * https://github.com/prisma/prisma-client-js/issues/707
   */
  export interface Prisma__RiskAssessmentClient<T, Null = never, ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> extends Prisma.PrismaPromise<T> {
    readonly [Symbol.toStringTag]: "PrismaPromise"
    simulation<T extends SimulationDefaultArgs<ExtArgs> = {}>(args?: Subset<T, SimulationDefaultArgs<ExtArgs>>): Prisma__SimulationClient<$Result.GetResult<Prisma.$SimulationPayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions> | Null, Null, ExtArgs, GlobalOmitOptions>
    /**
     * Attaches callbacks for the resolution and/or rejection of the Promise.
     * @param onfulfilled The callback to execute when the Promise is resolved.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of which ever callback is executed.
     */
    then<TResult1 = T, TResult2 = never>(onfulfilled?: ((value: T) => TResult1 | PromiseLike<TResult1>) | undefined | null, onrejected?: ((reason: any) => TResult2 | PromiseLike<TResult2>) | undefined | null): $Utils.JsPromise<TResult1 | TResult2>
    /**
     * Attaches a callback for only the rejection of the Promise.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of the callback.
     */
    catch<TResult = never>(onrejected?: ((reason: any) => TResult | PromiseLike<TResult>) | undefined | null): $Utils.JsPromise<T | TResult>
    /**
     * Attaches a callback that is invoked when the Promise is settled (fulfilled or rejected). The
     * resolved value cannot be modified from the callback.
     * @param onfinally The callback to execute when the Promise is settled (fulfilled or rejected).
     * @returns A Promise for the completion of the callback.
     */
    finally(onfinally?: (() => void) | undefined | null): $Utils.JsPromise<T>
  }




  /**
   * Fields of the RiskAssessment model
   */
  interface RiskAssessmentFieldRefs {
    readonly id: FieldRef<"RiskAssessment", 'Int'>
    readonly createdAt: FieldRef<"RiskAssessment", 'DateTime'>
    readonly updatedAt: FieldRef<"RiskAssessment", 'DateTime'>
    readonly simulationId: FieldRef<"RiskAssessment", 'Int'>
    readonly assessment: FieldRef<"RiskAssessment", 'Json'>
  }
    

  // Custom InputTypes
  /**
   * RiskAssessment findUnique
   */
  export type RiskAssessmentFindUniqueArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the RiskAssessment
     */
    select?: RiskAssessmentSelect<ExtArgs> | null
    /**
     * Omit specific fields from the RiskAssessment
     */
    omit?: RiskAssessmentOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: RiskAssessmentInclude<ExtArgs> | null
    /**
     * Filter, which RiskAssessment to fetch.
     */
    where: RiskAssessmentWhereUniqueInput
  }

  /**
   * RiskAssessment findUniqueOrThrow
   */
  export type RiskAssessmentFindUniqueOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the RiskAssessment
     */
    select?: RiskAssessmentSelect<ExtArgs> | null
    /**
     * Omit specific fields from the RiskAssessment
     */
    omit?: RiskAssessmentOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: RiskAssessmentInclude<ExtArgs> | null
    /**
     * Filter, which RiskAssessment to fetch.
     */
    where: RiskAssessmentWhereUniqueInput
  }

  /**
   * RiskAssessment findFirst
   */
  export type RiskAssessmentFindFirstArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the RiskAssessment
     */
    select?: RiskAssessmentSelect<ExtArgs> | null
    /**
     * Omit specific fields from the RiskAssessment
     */
    omit?: RiskAssessmentOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: RiskAssessmentInclude<ExtArgs> | null
    /**
     * Filter, which RiskAssessment to fetch.
     */
    where?: RiskAssessmentWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of RiskAssessments to fetch.
     */
    orderBy?: RiskAssessmentOrderByWithRelationInput | RiskAssessmentOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for RiskAssessments.
     */
    cursor?: RiskAssessmentWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` RiskAssessments from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` RiskAssessments.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of RiskAssessments.
     */
    distinct?: RiskAssessmentScalarFieldEnum | RiskAssessmentScalarFieldEnum[]
  }

  /**
   * RiskAssessment findFirstOrThrow
   */
  export type RiskAssessmentFindFirstOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the RiskAssessment
     */
    select?: RiskAssessmentSelect<ExtArgs> | null
    /**
     * Omit specific fields from the RiskAssessment
     */
    omit?: RiskAssessmentOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: RiskAssessmentInclude<ExtArgs> | null
    /**
     * Filter, which RiskAssessment to fetch.
     */
    where?: RiskAssessmentWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of RiskAssessments to fetch.
     */
    orderBy?: RiskAssessmentOrderByWithRelationInput | RiskAssessmentOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for RiskAssessments.
     */
    cursor?: RiskAssessmentWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` RiskAssessments from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` RiskAssessments.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of RiskAssessments.
     */
    distinct?: RiskAssessmentScalarFieldEnum | RiskAssessmentScalarFieldEnum[]
  }

  /**
   * RiskAssessment findMany
   */
  export type RiskAssessmentFindManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the RiskAssessment
     */
    select?: RiskAssessmentSelect<ExtArgs> | null
    /**
     * Omit specific fields from the RiskAssessment
     */
    omit?: RiskAssessmentOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: RiskAssessmentInclude<ExtArgs> | null
    /**
     * Filter, which RiskAssessments to fetch.
     */
    where?: RiskAssessmentWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of RiskAssessments to fetch.
     */
    orderBy?: RiskAssessmentOrderByWithRelationInput | RiskAssessmentOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for listing RiskAssessments.
     */
    cursor?: RiskAssessmentWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` RiskAssessments from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` RiskAssessments.
     */
    skip?: number
    distinct?: RiskAssessmentScalarFieldEnum | RiskAssessmentScalarFieldEnum[]
  }

  /**
   * RiskAssessment create
   */
  export type RiskAssessmentCreateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the RiskAssessment
     */
    select?: RiskAssessmentSelect<ExtArgs> | null
    /**
     * Omit specific fields from the RiskAssessment
     */
    omit?: RiskAssessmentOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: RiskAssessmentInclude<ExtArgs> | null
    /**
     * The data needed to create a RiskAssessment.
     */
    data: XOR<RiskAssessmentCreateInput, RiskAssessmentUncheckedCreateInput>
  }

  /**
   * RiskAssessment createMany
   */
  export type RiskAssessmentCreateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to create many RiskAssessments.
     */
    data: RiskAssessmentCreateManyInput | RiskAssessmentCreateManyInput[]
    skipDuplicates?: boolean
  }

  /**
   * RiskAssessment createManyAndReturn
   */
  export type RiskAssessmentCreateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the RiskAssessment
     */
    select?: RiskAssessmentSelectCreateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the RiskAssessment
     */
    omit?: RiskAssessmentOmit<ExtArgs> | null
    /**
     * The data used to create many RiskAssessments.
     */
    data: RiskAssessmentCreateManyInput | RiskAssessmentCreateManyInput[]
    skipDuplicates?: boolean
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: RiskAssessmentIncludeCreateManyAndReturn<ExtArgs> | null
  }

  /**
   * RiskAssessment update
   */
  export type RiskAssessmentUpdateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the RiskAssessment
     */
    select?: RiskAssessmentSelect<ExtArgs> | null
    /**
     * Omit specific fields from the RiskAssessment
     */
    omit?: RiskAssessmentOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: RiskAssessmentInclude<ExtArgs> | null
    /**
     * The data needed to update a RiskAssessment.
     */
    data: XOR<RiskAssessmentUpdateInput, RiskAssessmentUncheckedUpdateInput>
    /**
     * Choose, which RiskAssessment to update.
     */
    where: RiskAssessmentWhereUniqueInput
  }

  /**
   * RiskAssessment updateMany
   */
  export type RiskAssessmentUpdateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to update RiskAssessments.
     */
    data: XOR<RiskAssessmentUpdateManyMutationInput, RiskAssessmentUncheckedUpdateManyInput>
    /**
     * Filter which RiskAssessments to update
     */
    where?: RiskAssessmentWhereInput
    /**
     * Limit how many RiskAssessments to update.
     */
    limit?: number
  }

  /**
   * RiskAssessment updateManyAndReturn
   */
  export type RiskAssessmentUpdateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the RiskAssessment
     */
    select?: RiskAssessmentSelectUpdateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the RiskAssessment
     */
    omit?: RiskAssessmentOmit<ExtArgs> | null
    /**
     * The data used to update RiskAssessments.
     */
    data: XOR<RiskAssessmentUpdateManyMutationInput, RiskAssessmentUncheckedUpdateManyInput>
    /**
     * Filter which RiskAssessments to update
     */
    where?: RiskAssessmentWhereInput
    /**
     * Limit how many RiskAssessments to update.
     */
    limit?: number
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: RiskAssessmentIncludeUpdateManyAndReturn<ExtArgs> | null
  }

  /**
   * RiskAssessment upsert
   */
  export type RiskAssessmentUpsertArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the RiskAssessment
     */
    select?: RiskAssessmentSelect<ExtArgs> | null
    /**
     * Omit specific fields from the RiskAssessment
     */
    omit?: RiskAssessmentOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: RiskAssessmentInclude<ExtArgs> | null
    /**
     * The filter to search for the RiskAssessment to update in case it exists.
     */
    where: RiskAssessmentWhereUniqueInput
    /**
     * In case the RiskAssessment found by the `where` argument doesn't exist, create a new RiskAssessment with this data.
     */
    create: XOR<RiskAssessmentCreateInput, RiskAssessmentUncheckedCreateInput>
    /**
     * In case the RiskAssessment was found with the provided `where` argument, update it with this data.
     */
    update: XOR<RiskAssessmentUpdateInput, RiskAssessmentUncheckedUpdateInput>
  }

  /**
   * RiskAssessment delete
   */
  export type RiskAssessmentDeleteArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the RiskAssessment
     */
    select?: RiskAssessmentSelect<ExtArgs> | null
    /**
     * Omit specific fields from the RiskAssessment
     */
    omit?: RiskAssessmentOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: RiskAssessmentInclude<ExtArgs> | null
    /**
     * Filter which RiskAssessment to delete.
     */
    where: RiskAssessmentWhereUniqueInput
  }

  /**
   * RiskAssessment deleteMany
   */
  export type RiskAssessmentDeleteManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which RiskAssessments to delete
     */
    where?: RiskAssessmentWhereInput
    /**
     * Limit how many RiskAssessments to delete.
     */
    limit?: number
  }

  /**
   * RiskAssessment without action
   */
  export type RiskAssessmentDefaultArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the RiskAssessment
     */
    select?: RiskAssessmentSelect<ExtArgs> | null
    /**
     * Omit specific fields from the RiskAssessment
     */
    omit?: RiskAssessmentOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: RiskAssessmentInclude<ExtArgs> | null
  }


  /**
   * Model AuditLog
   */

  export type AggregateAuditLog = {
    _count: AuditLogCountAggregateOutputType | null
    _avg: AuditLogAvgAggregateOutputType | null
    _sum: AuditLogSumAggregateOutputType | null
    _min: AuditLogMinAggregateOutputType | null
    _max: AuditLogMaxAggregateOutputType | null
  }

  export type AuditLogAvgAggregateOutputType = {
    id: number | null
    userId: number | null
    simulationId: number | null
  }

  export type AuditLogSumAggregateOutputType = {
    id: number | null
    userId: number | null
    simulationId: number | null
  }

  export type AuditLogMinAggregateOutputType = {
    id: number | null
    createdAt: Date | null
    userId: number | null
    simulationId: number | null
    action: string | null
    ipAddress: string | null
    userAgent: string | null
  }

  export type AuditLogMaxAggregateOutputType = {
    id: number | null
    createdAt: Date | null
    userId: number | null
    simulationId: number | null
    action: string | null
    ipAddress: string | null
    userAgent: string | null
  }

  export type AuditLogCountAggregateOutputType = {
    id: number
    createdAt: number
    userId: number
    simulationId: number
    action: number
    details: number
    ipAddress: number
    userAgent: number
    _all: number
  }


  export type AuditLogAvgAggregateInputType = {
    id?: true
    userId?: true
    simulationId?: true
  }

  export type AuditLogSumAggregateInputType = {
    id?: true
    userId?: true
    simulationId?: true
  }

  export type AuditLogMinAggregateInputType = {
    id?: true
    createdAt?: true
    userId?: true
    simulationId?: true
    action?: true
    ipAddress?: true
    userAgent?: true
  }

  export type AuditLogMaxAggregateInputType = {
    id?: true
    createdAt?: true
    userId?: true
    simulationId?: true
    action?: true
    ipAddress?: true
    userAgent?: true
  }

  export type AuditLogCountAggregateInputType = {
    id?: true
    createdAt?: true
    userId?: true
    simulationId?: true
    action?: true
    details?: true
    ipAddress?: true
    userAgent?: true
    _all?: true
  }

  export type AuditLogAggregateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which AuditLog to aggregate.
     */
    where?: AuditLogWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of AuditLogs to fetch.
     */
    orderBy?: AuditLogOrderByWithRelationInput | AuditLogOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the start position
     */
    cursor?: AuditLogWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` AuditLogs from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` AuditLogs.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Count returned AuditLogs
    **/
    _count?: true | AuditLogCountAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to average
    **/
    _avg?: AuditLogAvgAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to sum
    **/
    _sum?: AuditLogSumAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the minimum value
    **/
    _min?: AuditLogMinAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the maximum value
    **/
    _max?: AuditLogMaxAggregateInputType
  }

  export type GetAuditLogAggregateType<T extends AuditLogAggregateArgs> = {
        [P in keyof T & keyof AggregateAuditLog]: P extends '_count' | 'count'
      ? T[P] extends true
        ? number
        : GetScalarType<T[P], AggregateAuditLog[P]>
      : GetScalarType<T[P], AggregateAuditLog[P]>
  }




  export type AuditLogGroupByArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: AuditLogWhereInput
    orderBy?: AuditLogOrderByWithAggregationInput | AuditLogOrderByWithAggregationInput[]
    by: AuditLogScalarFieldEnum[] | AuditLogScalarFieldEnum
    having?: AuditLogScalarWhereWithAggregatesInput
    take?: number
    skip?: number
    _count?: AuditLogCountAggregateInputType | true
    _avg?: AuditLogAvgAggregateInputType
    _sum?: AuditLogSumAggregateInputType
    _min?: AuditLogMinAggregateInputType
    _max?: AuditLogMaxAggregateInputType
  }

  export type AuditLogGroupByOutputType = {
    id: number
    createdAt: Date
    userId: number
    simulationId: number | null
    action: string
    details: JsonValue
    ipAddress: string
    userAgent: string
    _count: AuditLogCountAggregateOutputType | null
    _avg: AuditLogAvgAggregateOutputType | null
    _sum: AuditLogSumAggregateOutputType | null
    _min: AuditLogMinAggregateOutputType | null
    _max: AuditLogMaxAggregateOutputType | null
  }

  type GetAuditLogGroupByPayload<T extends AuditLogGroupByArgs> = Prisma.PrismaPromise<
    Array<
      PickEnumerable<AuditLogGroupByOutputType, T['by']> &
        {
          [P in ((keyof T) & (keyof AuditLogGroupByOutputType))]: P extends '_count'
            ? T[P] extends boolean
              ? number
              : GetScalarType<T[P], AuditLogGroupByOutputType[P]>
            : GetScalarType<T[P], AuditLogGroupByOutputType[P]>
        }
      >
    >


  export type AuditLogSelect<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    createdAt?: boolean
    userId?: boolean
    simulationId?: boolean
    action?: boolean
    details?: boolean
    ipAddress?: boolean
    userAgent?: boolean
    user?: boolean | UserDefaultArgs<ExtArgs>
    simulation?: boolean | AuditLog$simulationArgs<ExtArgs>
  }, ExtArgs["result"]["auditLog"]>

  export type AuditLogSelectCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    createdAt?: boolean
    userId?: boolean
    simulationId?: boolean
    action?: boolean
    details?: boolean
    ipAddress?: boolean
    userAgent?: boolean
    user?: boolean | UserDefaultArgs<ExtArgs>
    simulation?: boolean | AuditLog$simulationArgs<ExtArgs>
  }, ExtArgs["result"]["auditLog"]>

  export type AuditLogSelectUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    createdAt?: boolean
    userId?: boolean
    simulationId?: boolean
    action?: boolean
    details?: boolean
    ipAddress?: boolean
    userAgent?: boolean
    user?: boolean | UserDefaultArgs<ExtArgs>
    simulation?: boolean | AuditLog$simulationArgs<ExtArgs>
  }, ExtArgs["result"]["auditLog"]>

  export type AuditLogSelectScalar = {
    id?: boolean
    createdAt?: boolean
    userId?: boolean
    simulationId?: boolean
    action?: boolean
    details?: boolean
    ipAddress?: boolean
    userAgent?: boolean
  }

  export type AuditLogOmit<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetOmit<"id" | "createdAt" | "userId" | "simulationId" | "action" | "details" | "ipAddress" | "userAgent", ExtArgs["result"]["auditLog"]>
  export type AuditLogInclude<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    user?: boolean | UserDefaultArgs<ExtArgs>
    simulation?: boolean | AuditLog$simulationArgs<ExtArgs>
  }
  export type AuditLogIncludeCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    user?: boolean | UserDefaultArgs<ExtArgs>
    simulation?: boolean | AuditLog$simulationArgs<ExtArgs>
  }
  export type AuditLogIncludeUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    user?: boolean | UserDefaultArgs<ExtArgs>
    simulation?: boolean | AuditLog$simulationArgs<ExtArgs>
  }

  export type $AuditLogPayload<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    name: "AuditLog"
    objects: {
      user: Prisma.$UserPayload<ExtArgs>
      simulation: Prisma.$SimulationPayload<ExtArgs> | null
    }
    scalars: $Extensions.GetPayloadResult<{
      id: number
      createdAt: Date
      userId: number
      simulationId: number | null
      action: string
      details: Prisma.JsonValue
      ipAddress: string
      userAgent: string
    }, ExtArgs["result"]["auditLog"]>
    composites: {}
  }

  type AuditLogGetPayload<S extends boolean | null | undefined | AuditLogDefaultArgs> = $Result.GetResult<Prisma.$AuditLogPayload, S>

  type AuditLogCountArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> =
    Omit<AuditLogFindManyArgs, 'select' | 'include' | 'distinct' | 'omit'> & {
      select?: AuditLogCountAggregateInputType | true
    }

  export interface AuditLogDelegate<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> {
    [K: symbol]: { types: Prisma.TypeMap<ExtArgs>['model']['AuditLog'], meta: { name: 'AuditLog' } }
    /**
     * Find zero or one AuditLog that matches the filter.
     * @param {AuditLogFindUniqueArgs} args - Arguments to find a AuditLog
     * @example
     * // Get one AuditLog
     * const auditLog = await prisma.auditLog.findUnique({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUnique<T extends AuditLogFindUniqueArgs>(args: SelectSubset<T, AuditLogFindUniqueArgs<ExtArgs>>): Prisma__AuditLogClient<$Result.GetResult<Prisma.$AuditLogPayload<ExtArgs>, T, "findUnique", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find one AuditLog that matches the filter or throw an error with `error.code='P2025'`
     * if no matches were found.
     * @param {AuditLogFindUniqueOrThrowArgs} args - Arguments to find a AuditLog
     * @example
     * // Get one AuditLog
     * const auditLog = await prisma.auditLog.findUniqueOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUniqueOrThrow<T extends AuditLogFindUniqueOrThrowArgs>(args: SelectSubset<T, AuditLogFindUniqueOrThrowArgs<ExtArgs>>): Prisma__AuditLogClient<$Result.GetResult<Prisma.$AuditLogPayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first AuditLog that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {AuditLogFindFirstArgs} args - Arguments to find a AuditLog
     * @example
     * // Get one AuditLog
     * const auditLog = await prisma.auditLog.findFirst({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirst<T extends AuditLogFindFirstArgs>(args?: SelectSubset<T, AuditLogFindFirstArgs<ExtArgs>>): Prisma__AuditLogClient<$Result.GetResult<Prisma.$AuditLogPayload<ExtArgs>, T, "findFirst", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first AuditLog that matches the filter or
     * throw `PrismaKnownClientError` with `P2025` code if no matches were found.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {AuditLogFindFirstOrThrowArgs} args - Arguments to find a AuditLog
     * @example
     * // Get one AuditLog
     * const auditLog = await prisma.auditLog.findFirstOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirstOrThrow<T extends AuditLogFindFirstOrThrowArgs>(args?: SelectSubset<T, AuditLogFindFirstOrThrowArgs<ExtArgs>>): Prisma__AuditLogClient<$Result.GetResult<Prisma.$AuditLogPayload<ExtArgs>, T, "findFirstOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find zero or more AuditLogs that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {AuditLogFindManyArgs} args - Arguments to filter and select certain fields only.
     * @example
     * // Get all AuditLogs
     * const auditLogs = await prisma.auditLog.findMany()
     * 
     * // Get first 10 AuditLogs
     * const auditLogs = await prisma.auditLog.findMany({ take: 10 })
     * 
     * // Only select the `id`
     * const auditLogWithIdOnly = await prisma.auditLog.findMany({ select: { id: true } })
     * 
     */
    findMany<T extends AuditLogFindManyArgs>(args?: SelectSubset<T, AuditLogFindManyArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$AuditLogPayload<ExtArgs>, T, "findMany", GlobalOmitOptions>>

    /**
     * Create a AuditLog.
     * @param {AuditLogCreateArgs} args - Arguments to create a AuditLog.
     * @example
     * // Create one AuditLog
     * const AuditLog = await prisma.auditLog.create({
     *   data: {
     *     // ... data to create a AuditLog
     *   }
     * })
     * 
     */
    create<T extends AuditLogCreateArgs>(args: SelectSubset<T, AuditLogCreateArgs<ExtArgs>>): Prisma__AuditLogClient<$Result.GetResult<Prisma.$AuditLogPayload<ExtArgs>, T, "create", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Create many AuditLogs.
     * @param {AuditLogCreateManyArgs} args - Arguments to create many AuditLogs.
     * @example
     * // Create many AuditLogs
     * const auditLog = await prisma.auditLog.createMany({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     *     
     */
    createMany<T extends AuditLogCreateManyArgs>(args?: SelectSubset<T, AuditLogCreateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Create many AuditLogs and returns the data saved in the database.
     * @param {AuditLogCreateManyAndReturnArgs} args - Arguments to create many AuditLogs.
     * @example
     * // Create many AuditLogs
     * const auditLog = await prisma.auditLog.createManyAndReturn({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Create many AuditLogs and only return the `id`
     * const auditLogWithIdOnly = await prisma.auditLog.createManyAndReturn({
     *   select: { id: true },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    createManyAndReturn<T extends AuditLogCreateManyAndReturnArgs>(args?: SelectSubset<T, AuditLogCreateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$AuditLogPayload<ExtArgs>, T, "createManyAndReturn", GlobalOmitOptions>>

    /**
     * Delete a AuditLog.
     * @param {AuditLogDeleteArgs} args - Arguments to delete one AuditLog.
     * @example
     * // Delete one AuditLog
     * const AuditLog = await prisma.auditLog.delete({
     *   where: {
     *     // ... filter to delete one AuditLog
     *   }
     * })
     * 
     */
    delete<T extends AuditLogDeleteArgs>(args: SelectSubset<T, AuditLogDeleteArgs<ExtArgs>>): Prisma__AuditLogClient<$Result.GetResult<Prisma.$AuditLogPayload<ExtArgs>, T, "delete", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Update one AuditLog.
     * @param {AuditLogUpdateArgs} args - Arguments to update one AuditLog.
     * @example
     * // Update one AuditLog
     * const auditLog = await prisma.auditLog.update({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    update<T extends AuditLogUpdateArgs>(args: SelectSubset<T, AuditLogUpdateArgs<ExtArgs>>): Prisma__AuditLogClient<$Result.GetResult<Prisma.$AuditLogPayload<ExtArgs>, T, "update", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Delete zero or more AuditLogs.
     * @param {AuditLogDeleteManyArgs} args - Arguments to filter AuditLogs to delete.
     * @example
     * // Delete a few AuditLogs
     * const { count } = await prisma.auditLog.deleteMany({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     * 
     */
    deleteMany<T extends AuditLogDeleteManyArgs>(args?: SelectSubset<T, AuditLogDeleteManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more AuditLogs.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {AuditLogUpdateManyArgs} args - Arguments to update one or more rows.
     * @example
     * // Update many AuditLogs
     * const auditLog = await prisma.auditLog.updateMany({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    updateMany<T extends AuditLogUpdateManyArgs>(args: SelectSubset<T, AuditLogUpdateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more AuditLogs and returns the data updated in the database.
     * @param {AuditLogUpdateManyAndReturnArgs} args - Arguments to update many AuditLogs.
     * @example
     * // Update many AuditLogs
     * const auditLog = await prisma.auditLog.updateManyAndReturn({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Update zero or more AuditLogs and only return the `id`
     * const auditLogWithIdOnly = await prisma.auditLog.updateManyAndReturn({
     *   select: { id: true },
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    updateManyAndReturn<T extends AuditLogUpdateManyAndReturnArgs>(args: SelectSubset<T, AuditLogUpdateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$AuditLogPayload<ExtArgs>, T, "updateManyAndReturn", GlobalOmitOptions>>

    /**
     * Create or update one AuditLog.
     * @param {AuditLogUpsertArgs} args - Arguments to update or create a AuditLog.
     * @example
     * // Update or create a AuditLog
     * const auditLog = await prisma.auditLog.upsert({
     *   create: {
     *     // ... data to create a AuditLog
     *   },
     *   update: {
     *     // ... in case it already exists, update
     *   },
     *   where: {
     *     // ... the filter for the AuditLog we want to update
     *   }
     * })
     */
    upsert<T extends AuditLogUpsertArgs>(args: SelectSubset<T, AuditLogUpsertArgs<ExtArgs>>): Prisma__AuditLogClient<$Result.GetResult<Prisma.$AuditLogPayload<ExtArgs>, T, "upsert", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>


    /**
     * Count the number of AuditLogs.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {AuditLogCountArgs} args - Arguments to filter AuditLogs to count.
     * @example
     * // Count the number of AuditLogs
     * const count = await prisma.auditLog.count({
     *   where: {
     *     // ... the filter for the AuditLogs we want to count
     *   }
     * })
    **/
    count<T extends AuditLogCountArgs>(
      args?: Subset<T, AuditLogCountArgs>,
    ): Prisma.PrismaPromise<
      T extends $Utils.Record<'select', any>
        ? T['select'] extends true
          ? number
          : GetScalarType<T['select'], AuditLogCountAggregateOutputType>
        : number
    >

    /**
     * Allows you to perform aggregations operations on a AuditLog.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {AuditLogAggregateArgs} args - Select which aggregations you would like to apply and on what fields.
     * @example
     * // Ordered by age ascending
     * // Where email contains prisma.io
     * // Limited to the 10 users
     * const aggregations = await prisma.user.aggregate({
     *   _avg: {
     *     age: true,
     *   },
     *   where: {
     *     email: {
     *       contains: "prisma.io",
     *     },
     *   },
     *   orderBy: {
     *     age: "asc",
     *   },
     *   take: 10,
     * })
    **/
    aggregate<T extends AuditLogAggregateArgs>(args: Subset<T, AuditLogAggregateArgs>): Prisma.PrismaPromise<GetAuditLogAggregateType<T>>

    /**
     * Group by AuditLog.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {AuditLogGroupByArgs} args - Group by arguments.
     * @example
     * // Group by city, order by createdAt, get count
     * const result = await prisma.user.groupBy({
     *   by: ['city', 'createdAt'],
     *   orderBy: {
     *     createdAt: true
     *   },
     *   _count: {
     *     _all: true
     *   },
     * })
     * 
    **/
    groupBy<
      T extends AuditLogGroupByArgs,
      HasSelectOrTake extends Or<
        Extends<'skip', Keys<T>>,
        Extends<'take', Keys<T>>
      >,
      OrderByArg extends True extends HasSelectOrTake
        ? { orderBy: AuditLogGroupByArgs['orderBy'] }
        : { orderBy?: AuditLogGroupByArgs['orderBy'] },
      OrderFields extends ExcludeUnderscoreKeys<Keys<MaybeTupleToUnion<T['orderBy']>>>,
      ByFields extends MaybeTupleToUnion<T['by']>,
      ByValid extends Has<ByFields, OrderFields>,
      HavingFields extends GetHavingFields<T['having']>,
      HavingValid extends Has<ByFields, HavingFields>,
      ByEmpty extends T['by'] extends never[] ? True : False,
      InputErrors extends ByEmpty extends True
      ? `Error: "by" must not be empty.`
      : HavingValid extends False
      ? {
          [P in HavingFields]: P extends ByFields
            ? never
            : P extends string
            ? `Error: Field "${P}" used in "having" needs to be provided in "by".`
            : [
                Error,
                'Field ',
                P,
                ` in "having" needs to be provided in "by"`,
              ]
        }[HavingFields]
      : 'take' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "take", you also need to provide "orderBy"'
      : 'skip' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "skip", you also need to provide "orderBy"'
      : ByValid extends True
      ? {}
      : {
          [P in OrderFields]: P extends ByFields
            ? never
            : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
        }[OrderFields]
    >(args: SubsetIntersection<T, AuditLogGroupByArgs, OrderByArg> & InputErrors): {} extends InputErrors ? GetAuditLogGroupByPayload<T> : Prisma.PrismaPromise<InputErrors>
  /**
   * Fields of the AuditLog model
   */
  readonly fields: AuditLogFieldRefs;
  }

  /**
   * The delegate class that acts as a "Promise-like" for AuditLog.
   * Why is this prefixed with `Prisma__`?
   * Because we want to prevent naming conflicts as mentioned in
   * https://github.com/prisma/prisma-client-js/issues/707
   */
  export interface Prisma__AuditLogClient<T, Null = never, ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> extends Prisma.PrismaPromise<T> {
    readonly [Symbol.toStringTag]: "PrismaPromise"
    user<T extends UserDefaultArgs<ExtArgs> = {}>(args?: Subset<T, UserDefaultArgs<ExtArgs>>): Prisma__UserClient<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions> | Null, Null, ExtArgs, GlobalOmitOptions>
    simulation<T extends AuditLog$simulationArgs<ExtArgs> = {}>(args?: Subset<T, AuditLog$simulationArgs<ExtArgs>>): Prisma__SimulationClient<$Result.GetResult<Prisma.$SimulationPayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>
    /**
     * Attaches callbacks for the resolution and/or rejection of the Promise.
     * @param onfulfilled The callback to execute when the Promise is resolved.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of which ever callback is executed.
     */
    then<TResult1 = T, TResult2 = never>(onfulfilled?: ((value: T) => TResult1 | PromiseLike<TResult1>) | undefined | null, onrejected?: ((reason: any) => TResult2 | PromiseLike<TResult2>) | undefined | null): $Utils.JsPromise<TResult1 | TResult2>
    /**
     * Attaches a callback for only the rejection of the Promise.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of the callback.
     */
    catch<TResult = never>(onrejected?: ((reason: any) => TResult | PromiseLike<TResult>) | undefined | null): $Utils.JsPromise<T | TResult>
    /**
     * Attaches a callback that is invoked when the Promise is settled (fulfilled or rejected). The
     * resolved value cannot be modified from the callback.
     * @param onfinally The callback to execute when the Promise is settled (fulfilled or rejected).
     * @returns A Promise for the completion of the callback.
     */
    finally(onfinally?: (() => void) | undefined | null): $Utils.JsPromise<T>
  }




  /**
   * Fields of the AuditLog model
   */
  interface AuditLogFieldRefs {
    readonly id: FieldRef<"AuditLog", 'Int'>
    readonly createdAt: FieldRef<"AuditLog", 'DateTime'>
    readonly userId: FieldRef<"AuditLog", 'Int'>
    readonly simulationId: FieldRef<"AuditLog", 'Int'>
    readonly action: FieldRef<"AuditLog", 'String'>
    readonly details: FieldRef<"AuditLog", 'Json'>
    readonly ipAddress: FieldRef<"AuditLog", 'String'>
    readonly userAgent: FieldRef<"AuditLog", 'String'>
  }
    

  // Custom InputTypes
  /**
   * AuditLog findUnique
   */
  export type AuditLogFindUniqueArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the AuditLog
     */
    select?: AuditLogSelect<ExtArgs> | null
    /**
     * Omit specific fields from the AuditLog
     */
    omit?: AuditLogOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: AuditLogInclude<ExtArgs> | null
    /**
     * Filter, which AuditLog to fetch.
     */
    where: AuditLogWhereUniqueInput
  }

  /**
   * AuditLog findUniqueOrThrow
   */
  export type AuditLogFindUniqueOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the AuditLog
     */
    select?: AuditLogSelect<ExtArgs> | null
    /**
     * Omit specific fields from the AuditLog
     */
    omit?: AuditLogOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: AuditLogInclude<ExtArgs> | null
    /**
     * Filter, which AuditLog to fetch.
     */
    where: AuditLogWhereUniqueInput
  }

  /**
   * AuditLog findFirst
   */
  export type AuditLogFindFirstArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the AuditLog
     */
    select?: AuditLogSelect<ExtArgs> | null
    /**
     * Omit specific fields from the AuditLog
     */
    omit?: AuditLogOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: AuditLogInclude<ExtArgs> | null
    /**
     * Filter, which AuditLog to fetch.
     */
    where?: AuditLogWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of AuditLogs to fetch.
     */
    orderBy?: AuditLogOrderByWithRelationInput | AuditLogOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for AuditLogs.
     */
    cursor?: AuditLogWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` AuditLogs from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` AuditLogs.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of AuditLogs.
     */
    distinct?: AuditLogScalarFieldEnum | AuditLogScalarFieldEnum[]
  }

  /**
   * AuditLog findFirstOrThrow
   */
  export type AuditLogFindFirstOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the AuditLog
     */
    select?: AuditLogSelect<ExtArgs> | null
    /**
     * Omit specific fields from the AuditLog
     */
    omit?: AuditLogOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: AuditLogInclude<ExtArgs> | null
    /**
     * Filter, which AuditLog to fetch.
     */
    where?: AuditLogWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of AuditLogs to fetch.
     */
    orderBy?: AuditLogOrderByWithRelationInput | AuditLogOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for AuditLogs.
     */
    cursor?: AuditLogWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` AuditLogs from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` AuditLogs.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of AuditLogs.
     */
    distinct?: AuditLogScalarFieldEnum | AuditLogScalarFieldEnum[]
  }

  /**
   * AuditLog findMany
   */
  export type AuditLogFindManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the AuditLog
     */
    select?: AuditLogSelect<ExtArgs> | null
    /**
     * Omit specific fields from the AuditLog
     */
    omit?: AuditLogOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: AuditLogInclude<ExtArgs> | null
    /**
     * Filter, which AuditLogs to fetch.
     */
    where?: AuditLogWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of AuditLogs to fetch.
     */
    orderBy?: AuditLogOrderByWithRelationInput | AuditLogOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for listing AuditLogs.
     */
    cursor?: AuditLogWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` AuditLogs from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` AuditLogs.
     */
    skip?: number
    distinct?: AuditLogScalarFieldEnum | AuditLogScalarFieldEnum[]
  }

  /**
   * AuditLog create
   */
  export type AuditLogCreateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the AuditLog
     */
    select?: AuditLogSelect<ExtArgs> | null
    /**
     * Omit specific fields from the AuditLog
     */
    omit?: AuditLogOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: AuditLogInclude<ExtArgs> | null
    /**
     * The data needed to create a AuditLog.
     */
    data: XOR<AuditLogCreateInput, AuditLogUncheckedCreateInput>
  }

  /**
   * AuditLog createMany
   */
  export type AuditLogCreateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to create many AuditLogs.
     */
    data: AuditLogCreateManyInput | AuditLogCreateManyInput[]
    skipDuplicates?: boolean
  }

  /**
   * AuditLog createManyAndReturn
   */
  export type AuditLogCreateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the AuditLog
     */
    select?: AuditLogSelectCreateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the AuditLog
     */
    omit?: AuditLogOmit<ExtArgs> | null
    /**
     * The data used to create many AuditLogs.
     */
    data: AuditLogCreateManyInput | AuditLogCreateManyInput[]
    skipDuplicates?: boolean
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: AuditLogIncludeCreateManyAndReturn<ExtArgs> | null
  }

  /**
   * AuditLog update
   */
  export type AuditLogUpdateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the AuditLog
     */
    select?: AuditLogSelect<ExtArgs> | null
    /**
     * Omit specific fields from the AuditLog
     */
    omit?: AuditLogOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: AuditLogInclude<ExtArgs> | null
    /**
     * The data needed to update a AuditLog.
     */
    data: XOR<AuditLogUpdateInput, AuditLogUncheckedUpdateInput>
    /**
     * Choose, which AuditLog to update.
     */
    where: AuditLogWhereUniqueInput
  }

  /**
   * AuditLog updateMany
   */
  export type AuditLogUpdateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to update AuditLogs.
     */
    data: XOR<AuditLogUpdateManyMutationInput, AuditLogUncheckedUpdateManyInput>
    /**
     * Filter which AuditLogs to update
     */
    where?: AuditLogWhereInput
    /**
     * Limit how many AuditLogs to update.
     */
    limit?: number
  }

  /**
   * AuditLog updateManyAndReturn
   */
  export type AuditLogUpdateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the AuditLog
     */
    select?: AuditLogSelectUpdateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the AuditLog
     */
    omit?: AuditLogOmit<ExtArgs> | null
    /**
     * The data used to update AuditLogs.
     */
    data: XOR<AuditLogUpdateManyMutationInput, AuditLogUncheckedUpdateManyInput>
    /**
     * Filter which AuditLogs to update
     */
    where?: AuditLogWhereInput
    /**
     * Limit how many AuditLogs to update.
     */
    limit?: number
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: AuditLogIncludeUpdateManyAndReturn<ExtArgs> | null
  }

  /**
   * AuditLog upsert
   */
  export type AuditLogUpsertArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the AuditLog
     */
    select?: AuditLogSelect<ExtArgs> | null
    /**
     * Omit specific fields from the AuditLog
     */
    omit?: AuditLogOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: AuditLogInclude<ExtArgs> | null
    /**
     * The filter to search for the AuditLog to update in case it exists.
     */
    where: AuditLogWhereUniqueInput
    /**
     * In case the AuditLog found by the `where` argument doesn't exist, create a new AuditLog with this data.
     */
    create: XOR<AuditLogCreateInput, AuditLogUncheckedCreateInput>
    /**
     * In case the AuditLog was found with the provided `where` argument, update it with this data.
     */
    update: XOR<AuditLogUpdateInput, AuditLogUncheckedUpdateInput>
  }

  /**
   * AuditLog delete
   */
  export type AuditLogDeleteArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the AuditLog
     */
    select?: AuditLogSelect<ExtArgs> | null
    /**
     * Omit specific fields from the AuditLog
     */
    omit?: AuditLogOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: AuditLogInclude<ExtArgs> | null
    /**
     * Filter which AuditLog to delete.
     */
    where: AuditLogWhereUniqueInput
  }

  /**
   * AuditLog deleteMany
   */
  export type AuditLogDeleteManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which AuditLogs to delete
     */
    where?: AuditLogWhereInput
    /**
     * Limit how many AuditLogs to delete.
     */
    limit?: number
  }

  /**
   * AuditLog.simulation
   */
  export type AuditLog$simulationArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Simulation
     */
    select?: SimulationSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Simulation
     */
    omit?: SimulationOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: SimulationInclude<ExtArgs> | null
    where?: SimulationWhereInput
  }

  /**
   * AuditLog without action
   */
  export type AuditLogDefaultArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the AuditLog
     */
    select?: AuditLogSelect<ExtArgs> | null
    /**
     * Omit specific fields from the AuditLog
     */
    omit?: AuditLogOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: AuditLogInclude<ExtArgs> | null
  }


  /**
   * Enums
   */

  export const TransactionIsolationLevel: {
    ReadUncommitted: 'ReadUncommitted',
    ReadCommitted: 'ReadCommitted',
    RepeatableRead: 'RepeatableRead',
    Serializable: 'Serializable'
  };

  export type TransactionIsolationLevel = (typeof TransactionIsolationLevel)[keyof typeof TransactionIsolationLevel]


  export const UserScalarFieldEnum: {
    id: 'id',
    createdAt: 'createdAt',
    updatedAt: 'updatedAt',
    email: 'email',
    passwordHash: 'passwordHash',
    name: 'name',
    role: 'role'
  };

  export type UserScalarFieldEnum = (typeof UserScalarFieldEnum)[keyof typeof UserScalarFieldEnum]


  export const SimulationScalarFieldEnum: {
    id: 'id',
    createdAt: 'createdAt',
    updatedAt: 'updatedAt',
    name: 'name',
    description: 'description',
    status: 'status',
    userId: 'userId',
    config: 'config',
    modelType: 'modelType',
    version: 'version',
    tags: 'tags'
  };

  export type SimulationScalarFieldEnum = (typeof SimulationScalarFieldEnum)[keyof typeof SimulationScalarFieldEnum]


  export const BiasDetectionResultScalarFieldEnum: {
    id: 'id',
    createdAt: 'createdAt',
    updatedAt: 'updatedAt',
    simulationId: 'simulationId',
    result: 'result'
  };

  export type BiasDetectionResultScalarFieldEnum = (typeof BiasDetectionResultScalarFieldEnum)[keyof typeof BiasDetectionResultScalarFieldEnum]


  export const FairnessAssessmentScalarFieldEnum: {
    id: 'id',
    createdAt: 'createdAt',
    updatedAt: 'updatedAt',
    simulationId: 'simulationId',
    assessment: 'assessment'
  };

  export type FairnessAssessmentScalarFieldEnum = (typeof FairnessAssessmentScalarFieldEnum)[keyof typeof FairnessAssessmentScalarFieldEnum]


  export const ExplainabilityAnalysisScalarFieldEnum: {
    id: 'id',
    createdAt: 'createdAt',
    updatedAt: 'updatedAt',
    simulationId: 'simulationId',
    analysis: 'analysis'
  };

  export type ExplainabilityAnalysisScalarFieldEnum = (typeof ExplainabilityAnalysisScalarFieldEnum)[keyof typeof ExplainabilityAnalysisScalarFieldEnum]


  export const ComplianceRecordScalarFieldEnum: {
    id: 'id',
    createdAt: 'createdAt',
    updatedAt: 'updatedAt',
    simulationId: 'simulationId',
    record: 'record'
  };

  export type ComplianceRecordScalarFieldEnum = (typeof ComplianceRecordScalarFieldEnum)[keyof typeof ComplianceRecordScalarFieldEnum]


  export const RiskAssessmentScalarFieldEnum: {
    id: 'id',
    createdAt: 'createdAt',
    updatedAt: 'updatedAt',
    simulationId: 'simulationId',
    assessment: 'assessment'
  };

  export type RiskAssessmentScalarFieldEnum = (typeof RiskAssessmentScalarFieldEnum)[keyof typeof RiskAssessmentScalarFieldEnum]


  export const AuditLogScalarFieldEnum: {
    id: 'id',
    createdAt: 'createdAt',
    userId: 'userId',
    simulationId: 'simulationId',
    action: 'action',
    details: 'details',
    ipAddress: 'ipAddress',
    userAgent: 'userAgent'
  };

  export type AuditLogScalarFieldEnum = (typeof AuditLogScalarFieldEnum)[keyof typeof AuditLogScalarFieldEnum]


  export const SortOrder: {
    asc: 'asc',
    desc: 'desc'
  };

  export type SortOrder = (typeof SortOrder)[keyof typeof SortOrder]


  export const JsonNullValueInput: {
    JsonNull: typeof JsonNull
  };

  export type JsonNullValueInput = (typeof JsonNullValueInput)[keyof typeof JsonNullValueInput]


  export const QueryMode: {
    default: 'default',
    insensitive: 'insensitive'
  };

  export type QueryMode = (typeof QueryMode)[keyof typeof QueryMode]


  export const JsonNullValueFilter: {
    DbNull: typeof DbNull,
    JsonNull: typeof JsonNull,
    AnyNull: typeof AnyNull
  };

  export type JsonNullValueFilter = (typeof JsonNullValueFilter)[keyof typeof JsonNullValueFilter]


  export const NullsOrder: {
    first: 'first',
    last: 'last'
  };

  export type NullsOrder = (typeof NullsOrder)[keyof typeof NullsOrder]


  /**
   * Field references
   */


  /**
   * Reference to a field of type 'Int'
   */
  export type IntFieldRefInput<$PrismaModel> = FieldRefInputType<$PrismaModel, 'Int'>
    


  /**
   * Reference to a field of type 'Int[]'
   */
  export type ListIntFieldRefInput<$PrismaModel> = FieldRefInputType<$PrismaModel, 'Int[]'>
    


  /**
   * Reference to a field of type 'DateTime'
   */
  export type DateTimeFieldRefInput<$PrismaModel> = FieldRefInputType<$PrismaModel, 'DateTime'>
    


  /**
   * Reference to a field of type 'DateTime[]'
   */
  export type ListDateTimeFieldRefInput<$PrismaModel> = FieldRefInputType<$PrismaModel, 'DateTime[]'>
    


  /**
   * Reference to a field of type 'String'
   */
  export type StringFieldRefInput<$PrismaModel> = FieldRefInputType<$PrismaModel, 'String'>
    


  /**
   * Reference to a field of type 'String[]'
   */
  export type ListStringFieldRefInput<$PrismaModel> = FieldRefInputType<$PrismaModel, 'String[]'>
    


  /**
   * Reference to a field of type 'SimulationStatus'
   */
  export type EnumSimulationStatusFieldRefInput<$PrismaModel> = FieldRefInputType<$PrismaModel, 'SimulationStatus'>
    


  /**
   * Reference to a field of type 'SimulationStatus[]'
   */
  export type ListEnumSimulationStatusFieldRefInput<$PrismaModel> = FieldRefInputType<$PrismaModel, 'SimulationStatus[]'>
    


  /**
   * Reference to a field of type 'Json'
   */
  export type JsonFieldRefInput<$PrismaModel> = FieldRefInputType<$PrismaModel, 'Json'>
    


  /**
   * Reference to a field of type 'QueryMode'
   */
  export type EnumQueryModeFieldRefInput<$PrismaModel> = FieldRefInputType<$PrismaModel, 'QueryMode'>
    


  /**
   * Reference to a field of type 'Float'
   */
  export type FloatFieldRefInput<$PrismaModel> = FieldRefInputType<$PrismaModel, 'Float'>
    


  /**
   * Reference to a field of type 'Float[]'
   */
  export type ListFloatFieldRefInput<$PrismaModel> = FieldRefInputType<$PrismaModel, 'Float[]'>
    
  /**
   * Deep Input Types
   */


  export type UserWhereInput = {
    AND?: UserWhereInput | UserWhereInput[]
    OR?: UserWhereInput[]
    NOT?: UserWhereInput | UserWhereInput[]
    id?: IntFilter<"User"> | number
    createdAt?: DateTimeFilter<"User"> | Date | string
    updatedAt?: DateTimeFilter<"User"> | Date | string
    email?: StringFilter<"User"> | string
    passwordHash?: StringFilter<"User"> | string
    name?: StringFilter<"User"> | string
    role?: StringFilter<"User"> | string
    simulations?: SimulationListRelationFilter
    auditLogs?: AuditLogListRelationFilter
  }

  export type UserOrderByWithRelationInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    email?: SortOrder
    passwordHash?: SortOrder
    name?: SortOrder
    role?: SortOrder
    simulations?: SimulationOrderByRelationAggregateInput
    auditLogs?: AuditLogOrderByRelationAggregateInput
  }

  export type UserWhereUniqueInput = Prisma.AtLeast<{
    id?: number
    email?: string
    AND?: UserWhereInput | UserWhereInput[]
    OR?: UserWhereInput[]
    NOT?: UserWhereInput | UserWhereInput[]
    createdAt?: DateTimeFilter<"User"> | Date | string
    updatedAt?: DateTimeFilter<"User"> | Date | string
    passwordHash?: StringFilter<"User"> | string
    name?: StringFilter<"User"> | string
    role?: StringFilter<"User"> | string
    simulations?: SimulationListRelationFilter
    auditLogs?: AuditLogListRelationFilter
  }, "id" | "email">

  export type UserOrderByWithAggregationInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    email?: SortOrder
    passwordHash?: SortOrder
    name?: SortOrder
    role?: SortOrder
    _count?: UserCountOrderByAggregateInput
    _avg?: UserAvgOrderByAggregateInput
    _max?: UserMaxOrderByAggregateInput
    _min?: UserMinOrderByAggregateInput
    _sum?: UserSumOrderByAggregateInput
  }

  export type UserScalarWhereWithAggregatesInput = {
    AND?: UserScalarWhereWithAggregatesInput | UserScalarWhereWithAggregatesInput[]
    OR?: UserScalarWhereWithAggregatesInput[]
    NOT?: UserScalarWhereWithAggregatesInput | UserScalarWhereWithAggregatesInput[]
    id?: IntWithAggregatesFilter<"User"> | number
    createdAt?: DateTimeWithAggregatesFilter<"User"> | Date | string
    updatedAt?: DateTimeWithAggregatesFilter<"User"> | Date | string
    email?: StringWithAggregatesFilter<"User"> | string
    passwordHash?: StringWithAggregatesFilter<"User"> | string
    name?: StringWithAggregatesFilter<"User"> | string
    role?: StringWithAggregatesFilter<"User"> | string
  }

  export type SimulationWhereInput = {
    AND?: SimulationWhereInput | SimulationWhereInput[]
    OR?: SimulationWhereInput[]
    NOT?: SimulationWhereInput | SimulationWhereInput[]
    id?: IntFilter<"Simulation"> | number
    createdAt?: DateTimeFilter<"Simulation"> | Date | string
    updatedAt?: DateTimeFilter<"Simulation"> | Date | string
    name?: StringFilter<"Simulation"> | string
    description?: StringNullableFilter<"Simulation"> | string | null
    status?: EnumSimulationStatusFilter<"Simulation"> | $Enums.SimulationStatus
    userId?: IntFilter<"Simulation"> | number
    config?: JsonFilter<"Simulation">
    modelType?: StringFilter<"Simulation"> | string
    version?: StringFilter<"Simulation"> | string
    tags?: StringNullableListFilter<"Simulation">
    user?: XOR<UserScalarRelationFilter, UserWhereInput>
    BiasDetectionResult?: BiasDetectionResultListRelationFilter
    FairnessAssessment?: FairnessAssessmentListRelationFilter
    ExplainabilityAnalysis?: ExplainabilityAnalysisListRelationFilter
    ComplianceRecord?: ComplianceRecordListRelationFilter
    RiskAssessment?: RiskAssessmentListRelationFilter
    auditLogs?: AuditLogListRelationFilter
  }

  export type SimulationOrderByWithRelationInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    name?: SortOrder
    description?: SortOrderInput | SortOrder
    status?: SortOrder
    userId?: SortOrder
    config?: SortOrder
    modelType?: SortOrder
    version?: SortOrder
    tags?: SortOrder
    user?: UserOrderByWithRelationInput
    BiasDetectionResult?: BiasDetectionResultOrderByRelationAggregateInput
    FairnessAssessment?: FairnessAssessmentOrderByRelationAggregateInput
    ExplainabilityAnalysis?: ExplainabilityAnalysisOrderByRelationAggregateInput
    ComplianceRecord?: ComplianceRecordOrderByRelationAggregateInput
    RiskAssessment?: RiskAssessmentOrderByRelationAggregateInput
    auditLogs?: AuditLogOrderByRelationAggregateInput
  }

  export type SimulationWhereUniqueInput = Prisma.AtLeast<{
    id?: number
    AND?: SimulationWhereInput | SimulationWhereInput[]
    OR?: SimulationWhereInput[]
    NOT?: SimulationWhereInput | SimulationWhereInput[]
    createdAt?: DateTimeFilter<"Simulation"> | Date | string
    updatedAt?: DateTimeFilter<"Simulation"> | Date | string
    name?: StringFilter<"Simulation"> | string
    description?: StringNullableFilter<"Simulation"> | string | null
    status?: EnumSimulationStatusFilter<"Simulation"> | $Enums.SimulationStatus
    userId?: IntFilter<"Simulation"> | number
    config?: JsonFilter<"Simulation">
    modelType?: StringFilter<"Simulation"> | string
    version?: StringFilter<"Simulation"> | string
    tags?: StringNullableListFilter<"Simulation">
    user?: XOR<UserScalarRelationFilter, UserWhereInput>
    BiasDetectionResult?: BiasDetectionResultListRelationFilter
    FairnessAssessment?: FairnessAssessmentListRelationFilter
    ExplainabilityAnalysis?: ExplainabilityAnalysisListRelationFilter
    ComplianceRecord?: ComplianceRecordListRelationFilter
    RiskAssessment?: RiskAssessmentListRelationFilter
    auditLogs?: AuditLogListRelationFilter
  }, "id">

  export type SimulationOrderByWithAggregationInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    name?: SortOrder
    description?: SortOrderInput | SortOrder
    status?: SortOrder
    userId?: SortOrder
    config?: SortOrder
    modelType?: SortOrder
    version?: SortOrder
    tags?: SortOrder
    _count?: SimulationCountOrderByAggregateInput
    _avg?: SimulationAvgOrderByAggregateInput
    _max?: SimulationMaxOrderByAggregateInput
    _min?: SimulationMinOrderByAggregateInput
    _sum?: SimulationSumOrderByAggregateInput
  }

  export type SimulationScalarWhereWithAggregatesInput = {
    AND?: SimulationScalarWhereWithAggregatesInput | SimulationScalarWhereWithAggregatesInput[]
    OR?: SimulationScalarWhereWithAggregatesInput[]
    NOT?: SimulationScalarWhereWithAggregatesInput | SimulationScalarWhereWithAggregatesInput[]
    id?: IntWithAggregatesFilter<"Simulation"> | number
    createdAt?: DateTimeWithAggregatesFilter<"Simulation"> | Date | string
    updatedAt?: DateTimeWithAggregatesFilter<"Simulation"> | Date | string
    name?: StringWithAggregatesFilter<"Simulation"> | string
    description?: StringNullableWithAggregatesFilter<"Simulation"> | string | null
    status?: EnumSimulationStatusWithAggregatesFilter<"Simulation"> | $Enums.SimulationStatus
    userId?: IntWithAggregatesFilter<"Simulation"> | number
    config?: JsonWithAggregatesFilter<"Simulation">
    modelType?: StringWithAggregatesFilter<"Simulation"> | string
    version?: StringWithAggregatesFilter<"Simulation"> | string
    tags?: StringNullableListFilter<"Simulation">
  }

  export type BiasDetectionResultWhereInput = {
    AND?: BiasDetectionResultWhereInput | BiasDetectionResultWhereInput[]
    OR?: BiasDetectionResultWhereInput[]
    NOT?: BiasDetectionResultWhereInput | BiasDetectionResultWhereInput[]
    id?: IntFilter<"BiasDetectionResult"> | number
    createdAt?: DateTimeFilter<"BiasDetectionResult"> | Date | string
    updatedAt?: DateTimeFilter<"BiasDetectionResult"> | Date | string
    simulationId?: IntFilter<"BiasDetectionResult"> | number
    result?: JsonFilter<"BiasDetectionResult">
    simulation?: XOR<SimulationScalarRelationFilter, SimulationWhereInput>
  }

  export type BiasDetectionResultOrderByWithRelationInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    simulationId?: SortOrder
    result?: SortOrder
    simulation?: SimulationOrderByWithRelationInput
  }

  export type BiasDetectionResultWhereUniqueInput = Prisma.AtLeast<{
    id?: number
    AND?: BiasDetectionResultWhereInput | BiasDetectionResultWhereInput[]
    OR?: BiasDetectionResultWhereInput[]
    NOT?: BiasDetectionResultWhereInput | BiasDetectionResultWhereInput[]
    createdAt?: DateTimeFilter<"BiasDetectionResult"> | Date | string
    updatedAt?: DateTimeFilter<"BiasDetectionResult"> | Date | string
    simulationId?: IntFilter<"BiasDetectionResult"> | number
    result?: JsonFilter<"BiasDetectionResult">
    simulation?: XOR<SimulationScalarRelationFilter, SimulationWhereInput>
  }, "id">

  export type BiasDetectionResultOrderByWithAggregationInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    simulationId?: SortOrder
    result?: SortOrder
    _count?: BiasDetectionResultCountOrderByAggregateInput
    _avg?: BiasDetectionResultAvgOrderByAggregateInput
    _max?: BiasDetectionResultMaxOrderByAggregateInput
    _min?: BiasDetectionResultMinOrderByAggregateInput
    _sum?: BiasDetectionResultSumOrderByAggregateInput
  }

  export type BiasDetectionResultScalarWhereWithAggregatesInput = {
    AND?: BiasDetectionResultScalarWhereWithAggregatesInput | BiasDetectionResultScalarWhereWithAggregatesInput[]
    OR?: BiasDetectionResultScalarWhereWithAggregatesInput[]
    NOT?: BiasDetectionResultScalarWhereWithAggregatesInput | BiasDetectionResultScalarWhereWithAggregatesInput[]
    id?: IntWithAggregatesFilter<"BiasDetectionResult"> | number
    createdAt?: DateTimeWithAggregatesFilter<"BiasDetectionResult"> | Date | string
    updatedAt?: DateTimeWithAggregatesFilter<"BiasDetectionResult"> | Date | string
    simulationId?: IntWithAggregatesFilter<"BiasDetectionResult"> | number
    result?: JsonWithAggregatesFilter<"BiasDetectionResult">
  }

  export type FairnessAssessmentWhereInput = {
    AND?: FairnessAssessmentWhereInput | FairnessAssessmentWhereInput[]
    OR?: FairnessAssessmentWhereInput[]
    NOT?: FairnessAssessmentWhereInput | FairnessAssessmentWhereInput[]
    id?: IntFilter<"FairnessAssessment"> | number
    createdAt?: DateTimeFilter<"FairnessAssessment"> | Date | string
    updatedAt?: DateTimeFilter<"FairnessAssessment"> | Date | string
    simulationId?: IntFilter<"FairnessAssessment"> | number
    assessment?: JsonFilter<"FairnessAssessment">
    simulation?: XOR<SimulationScalarRelationFilter, SimulationWhereInput>
  }

  export type FairnessAssessmentOrderByWithRelationInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    simulationId?: SortOrder
    assessment?: SortOrder
    simulation?: SimulationOrderByWithRelationInput
  }

  export type FairnessAssessmentWhereUniqueInput = Prisma.AtLeast<{
    id?: number
    AND?: FairnessAssessmentWhereInput | FairnessAssessmentWhereInput[]
    OR?: FairnessAssessmentWhereInput[]
    NOT?: FairnessAssessmentWhereInput | FairnessAssessmentWhereInput[]
    createdAt?: DateTimeFilter<"FairnessAssessment"> | Date | string
    updatedAt?: DateTimeFilter<"FairnessAssessment"> | Date | string
    simulationId?: IntFilter<"FairnessAssessment"> | number
    assessment?: JsonFilter<"FairnessAssessment">
    simulation?: XOR<SimulationScalarRelationFilter, SimulationWhereInput>
  }, "id">

  export type FairnessAssessmentOrderByWithAggregationInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    simulationId?: SortOrder
    assessment?: SortOrder
    _count?: FairnessAssessmentCountOrderByAggregateInput
    _avg?: FairnessAssessmentAvgOrderByAggregateInput
    _max?: FairnessAssessmentMaxOrderByAggregateInput
    _min?: FairnessAssessmentMinOrderByAggregateInput
    _sum?: FairnessAssessmentSumOrderByAggregateInput
  }

  export type FairnessAssessmentScalarWhereWithAggregatesInput = {
    AND?: FairnessAssessmentScalarWhereWithAggregatesInput | FairnessAssessmentScalarWhereWithAggregatesInput[]
    OR?: FairnessAssessmentScalarWhereWithAggregatesInput[]
    NOT?: FairnessAssessmentScalarWhereWithAggregatesInput | FairnessAssessmentScalarWhereWithAggregatesInput[]
    id?: IntWithAggregatesFilter<"FairnessAssessment"> | number
    createdAt?: DateTimeWithAggregatesFilter<"FairnessAssessment"> | Date | string
    updatedAt?: DateTimeWithAggregatesFilter<"FairnessAssessment"> | Date | string
    simulationId?: IntWithAggregatesFilter<"FairnessAssessment"> | number
    assessment?: JsonWithAggregatesFilter<"FairnessAssessment">
  }

  export type ExplainabilityAnalysisWhereInput = {
    AND?: ExplainabilityAnalysisWhereInput | ExplainabilityAnalysisWhereInput[]
    OR?: ExplainabilityAnalysisWhereInput[]
    NOT?: ExplainabilityAnalysisWhereInput | ExplainabilityAnalysisWhereInput[]
    id?: IntFilter<"ExplainabilityAnalysis"> | number
    createdAt?: DateTimeFilter<"ExplainabilityAnalysis"> | Date | string
    updatedAt?: DateTimeFilter<"ExplainabilityAnalysis"> | Date | string
    simulationId?: IntFilter<"ExplainabilityAnalysis"> | number
    analysis?: JsonFilter<"ExplainabilityAnalysis">
    simulation?: XOR<SimulationScalarRelationFilter, SimulationWhereInput>
  }

  export type ExplainabilityAnalysisOrderByWithRelationInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    simulationId?: SortOrder
    analysis?: SortOrder
    simulation?: SimulationOrderByWithRelationInput
  }

  export type ExplainabilityAnalysisWhereUniqueInput = Prisma.AtLeast<{
    id?: number
    AND?: ExplainabilityAnalysisWhereInput | ExplainabilityAnalysisWhereInput[]
    OR?: ExplainabilityAnalysisWhereInput[]
    NOT?: ExplainabilityAnalysisWhereInput | ExplainabilityAnalysisWhereInput[]
    createdAt?: DateTimeFilter<"ExplainabilityAnalysis"> | Date | string
    updatedAt?: DateTimeFilter<"ExplainabilityAnalysis"> | Date | string
    simulationId?: IntFilter<"ExplainabilityAnalysis"> | number
    analysis?: JsonFilter<"ExplainabilityAnalysis">
    simulation?: XOR<SimulationScalarRelationFilter, SimulationWhereInput>
  }, "id">

  export type ExplainabilityAnalysisOrderByWithAggregationInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    simulationId?: SortOrder
    analysis?: SortOrder
    _count?: ExplainabilityAnalysisCountOrderByAggregateInput
    _avg?: ExplainabilityAnalysisAvgOrderByAggregateInput
    _max?: ExplainabilityAnalysisMaxOrderByAggregateInput
    _min?: ExplainabilityAnalysisMinOrderByAggregateInput
    _sum?: ExplainabilityAnalysisSumOrderByAggregateInput
  }

  export type ExplainabilityAnalysisScalarWhereWithAggregatesInput = {
    AND?: ExplainabilityAnalysisScalarWhereWithAggregatesInput | ExplainabilityAnalysisScalarWhereWithAggregatesInput[]
    OR?: ExplainabilityAnalysisScalarWhereWithAggregatesInput[]
    NOT?: ExplainabilityAnalysisScalarWhereWithAggregatesInput | ExplainabilityAnalysisScalarWhereWithAggregatesInput[]
    id?: IntWithAggregatesFilter<"ExplainabilityAnalysis"> | number
    createdAt?: DateTimeWithAggregatesFilter<"ExplainabilityAnalysis"> | Date | string
    updatedAt?: DateTimeWithAggregatesFilter<"ExplainabilityAnalysis"> | Date | string
    simulationId?: IntWithAggregatesFilter<"ExplainabilityAnalysis"> | number
    analysis?: JsonWithAggregatesFilter<"ExplainabilityAnalysis">
  }

  export type ComplianceRecordWhereInput = {
    AND?: ComplianceRecordWhereInput | ComplianceRecordWhereInput[]
    OR?: ComplianceRecordWhereInput[]
    NOT?: ComplianceRecordWhereInput | ComplianceRecordWhereInput[]
    id?: IntFilter<"ComplianceRecord"> | number
    createdAt?: DateTimeFilter<"ComplianceRecord"> | Date | string
    updatedAt?: DateTimeFilter<"ComplianceRecord"> | Date | string
    simulationId?: IntFilter<"ComplianceRecord"> | number
    record?: JsonFilter<"ComplianceRecord">
    simulation?: XOR<SimulationScalarRelationFilter, SimulationWhereInput>
  }

  export type ComplianceRecordOrderByWithRelationInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    simulationId?: SortOrder
    record?: SortOrder
    simulation?: SimulationOrderByWithRelationInput
  }

  export type ComplianceRecordWhereUniqueInput = Prisma.AtLeast<{
    id?: number
    AND?: ComplianceRecordWhereInput | ComplianceRecordWhereInput[]
    OR?: ComplianceRecordWhereInput[]
    NOT?: ComplianceRecordWhereInput | ComplianceRecordWhereInput[]
    createdAt?: DateTimeFilter<"ComplianceRecord"> | Date | string
    updatedAt?: DateTimeFilter<"ComplianceRecord"> | Date | string
    simulationId?: IntFilter<"ComplianceRecord"> | number
    record?: JsonFilter<"ComplianceRecord">
    simulation?: XOR<SimulationScalarRelationFilter, SimulationWhereInput>
  }, "id">

  export type ComplianceRecordOrderByWithAggregationInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    simulationId?: SortOrder
    record?: SortOrder
    _count?: ComplianceRecordCountOrderByAggregateInput
    _avg?: ComplianceRecordAvgOrderByAggregateInput
    _max?: ComplianceRecordMaxOrderByAggregateInput
    _min?: ComplianceRecordMinOrderByAggregateInput
    _sum?: ComplianceRecordSumOrderByAggregateInput
  }

  export type ComplianceRecordScalarWhereWithAggregatesInput = {
    AND?: ComplianceRecordScalarWhereWithAggregatesInput | ComplianceRecordScalarWhereWithAggregatesInput[]
    OR?: ComplianceRecordScalarWhereWithAggregatesInput[]
    NOT?: ComplianceRecordScalarWhereWithAggregatesInput | ComplianceRecordScalarWhereWithAggregatesInput[]
    id?: IntWithAggregatesFilter<"ComplianceRecord"> | number
    createdAt?: DateTimeWithAggregatesFilter<"ComplianceRecord"> | Date | string
    updatedAt?: DateTimeWithAggregatesFilter<"ComplianceRecord"> | Date | string
    simulationId?: IntWithAggregatesFilter<"ComplianceRecord"> | number
    record?: JsonWithAggregatesFilter<"ComplianceRecord">
  }

  export type RiskAssessmentWhereInput = {
    AND?: RiskAssessmentWhereInput | RiskAssessmentWhereInput[]
    OR?: RiskAssessmentWhereInput[]
    NOT?: RiskAssessmentWhereInput | RiskAssessmentWhereInput[]
    id?: IntFilter<"RiskAssessment"> | number
    createdAt?: DateTimeFilter<"RiskAssessment"> | Date | string
    updatedAt?: DateTimeFilter<"RiskAssessment"> | Date | string
    simulationId?: IntFilter<"RiskAssessment"> | number
    assessment?: JsonFilter<"RiskAssessment">
    simulation?: XOR<SimulationScalarRelationFilter, SimulationWhereInput>
  }

  export type RiskAssessmentOrderByWithRelationInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    simulationId?: SortOrder
    assessment?: SortOrder
    simulation?: SimulationOrderByWithRelationInput
  }

  export type RiskAssessmentWhereUniqueInput = Prisma.AtLeast<{
    id?: number
    AND?: RiskAssessmentWhereInput | RiskAssessmentWhereInput[]
    OR?: RiskAssessmentWhereInput[]
    NOT?: RiskAssessmentWhereInput | RiskAssessmentWhereInput[]
    createdAt?: DateTimeFilter<"RiskAssessment"> | Date | string
    updatedAt?: DateTimeFilter<"RiskAssessment"> | Date | string
    simulationId?: IntFilter<"RiskAssessment"> | number
    assessment?: JsonFilter<"RiskAssessment">
    simulation?: XOR<SimulationScalarRelationFilter, SimulationWhereInput>
  }, "id">

  export type RiskAssessmentOrderByWithAggregationInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    simulationId?: SortOrder
    assessment?: SortOrder
    _count?: RiskAssessmentCountOrderByAggregateInput
    _avg?: RiskAssessmentAvgOrderByAggregateInput
    _max?: RiskAssessmentMaxOrderByAggregateInput
    _min?: RiskAssessmentMinOrderByAggregateInput
    _sum?: RiskAssessmentSumOrderByAggregateInput
  }

  export type RiskAssessmentScalarWhereWithAggregatesInput = {
    AND?: RiskAssessmentScalarWhereWithAggregatesInput | RiskAssessmentScalarWhereWithAggregatesInput[]
    OR?: RiskAssessmentScalarWhereWithAggregatesInput[]
    NOT?: RiskAssessmentScalarWhereWithAggregatesInput | RiskAssessmentScalarWhereWithAggregatesInput[]
    id?: IntWithAggregatesFilter<"RiskAssessment"> | number
    createdAt?: DateTimeWithAggregatesFilter<"RiskAssessment"> | Date | string
    updatedAt?: DateTimeWithAggregatesFilter<"RiskAssessment"> | Date | string
    simulationId?: IntWithAggregatesFilter<"RiskAssessment"> | number
    assessment?: JsonWithAggregatesFilter<"RiskAssessment">
  }

  export type AuditLogWhereInput = {
    AND?: AuditLogWhereInput | AuditLogWhereInput[]
    OR?: AuditLogWhereInput[]
    NOT?: AuditLogWhereInput | AuditLogWhereInput[]
    id?: IntFilter<"AuditLog"> | number
    createdAt?: DateTimeFilter<"AuditLog"> | Date | string
    userId?: IntFilter<"AuditLog"> | number
    simulationId?: IntNullableFilter<"AuditLog"> | number | null
    action?: StringFilter<"AuditLog"> | string
    details?: JsonFilter<"AuditLog">
    ipAddress?: StringFilter<"AuditLog"> | string
    userAgent?: StringFilter<"AuditLog"> | string
    user?: XOR<UserScalarRelationFilter, UserWhereInput>
    simulation?: XOR<SimulationNullableScalarRelationFilter, SimulationWhereInput> | null
  }

  export type AuditLogOrderByWithRelationInput = {
    id?: SortOrder
    createdAt?: SortOrder
    userId?: SortOrder
    simulationId?: SortOrderInput | SortOrder
    action?: SortOrder
    details?: SortOrder
    ipAddress?: SortOrder
    userAgent?: SortOrder
    user?: UserOrderByWithRelationInput
    simulation?: SimulationOrderByWithRelationInput
  }

  export type AuditLogWhereUniqueInput = Prisma.AtLeast<{
    id?: number
    AND?: AuditLogWhereInput | AuditLogWhereInput[]
    OR?: AuditLogWhereInput[]
    NOT?: AuditLogWhereInput | AuditLogWhereInput[]
    createdAt?: DateTimeFilter<"AuditLog"> | Date | string
    userId?: IntFilter<"AuditLog"> | number
    simulationId?: IntNullableFilter<"AuditLog"> | number | null
    action?: StringFilter<"AuditLog"> | string
    details?: JsonFilter<"AuditLog">
    ipAddress?: StringFilter<"AuditLog"> | string
    userAgent?: StringFilter<"AuditLog"> | string
    user?: XOR<UserScalarRelationFilter, UserWhereInput>
    simulation?: XOR<SimulationNullableScalarRelationFilter, SimulationWhereInput> | null
  }, "id">

  export type AuditLogOrderByWithAggregationInput = {
    id?: SortOrder
    createdAt?: SortOrder
    userId?: SortOrder
    simulationId?: SortOrderInput | SortOrder
    action?: SortOrder
    details?: SortOrder
    ipAddress?: SortOrder
    userAgent?: SortOrder
    _count?: AuditLogCountOrderByAggregateInput
    _avg?: AuditLogAvgOrderByAggregateInput
    _max?: AuditLogMaxOrderByAggregateInput
    _min?: AuditLogMinOrderByAggregateInput
    _sum?: AuditLogSumOrderByAggregateInput
  }

  export type AuditLogScalarWhereWithAggregatesInput = {
    AND?: AuditLogScalarWhereWithAggregatesInput | AuditLogScalarWhereWithAggregatesInput[]
    OR?: AuditLogScalarWhereWithAggregatesInput[]
    NOT?: AuditLogScalarWhereWithAggregatesInput | AuditLogScalarWhereWithAggregatesInput[]
    id?: IntWithAggregatesFilter<"AuditLog"> | number
    createdAt?: DateTimeWithAggregatesFilter<"AuditLog"> | Date | string
    userId?: IntWithAggregatesFilter<"AuditLog"> | number
    simulationId?: IntNullableWithAggregatesFilter<"AuditLog"> | number | null
    action?: StringWithAggregatesFilter<"AuditLog"> | string
    details?: JsonWithAggregatesFilter<"AuditLog">
    ipAddress?: StringWithAggregatesFilter<"AuditLog"> | string
    userAgent?: StringWithAggregatesFilter<"AuditLog"> | string
  }

  export type UserCreateInput = {
    createdAt?: Date | string
    updatedAt?: Date | string
    email: string
    passwordHash: string
    name: string
    role?: string
    simulations?: SimulationCreateNestedManyWithoutUserInput
    auditLogs?: AuditLogCreateNestedManyWithoutUserInput
  }

  export type UserUncheckedCreateInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    email: string
    passwordHash: string
    name: string
    role?: string
    simulations?: SimulationUncheckedCreateNestedManyWithoutUserInput
    auditLogs?: AuditLogUncheckedCreateNestedManyWithoutUserInput
  }

  export type UserUpdateInput = {
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    email?: StringFieldUpdateOperationsInput | string
    passwordHash?: StringFieldUpdateOperationsInput | string
    name?: StringFieldUpdateOperationsInput | string
    role?: StringFieldUpdateOperationsInput | string
    simulations?: SimulationUpdateManyWithoutUserNestedInput
    auditLogs?: AuditLogUpdateManyWithoutUserNestedInput
  }

  export type UserUncheckedUpdateInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    email?: StringFieldUpdateOperationsInput | string
    passwordHash?: StringFieldUpdateOperationsInput | string
    name?: StringFieldUpdateOperationsInput | string
    role?: StringFieldUpdateOperationsInput | string
    simulations?: SimulationUncheckedUpdateManyWithoutUserNestedInput
    auditLogs?: AuditLogUncheckedUpdateManyWithoutUserNestedInput
  }

  export type UserCreateManyInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    email: string
    passwordHash: string
    name: string
    role?: string
  }

  export type UserUpdateManyMutationInput = {
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    email?: StringFieldUpdateOperationsInput | string
    passwordHash?: StringFieldUpdateOperationsInput | string
    name?: StringFieldUpdateOperationsInput | string
    role?: StringFieldUpdateOperationsInput | string
  }

  export type UserUncheckedUpdateManyInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    email?: StringFieldUpdateOperationsInput | string
    passwordHash?: StringFieldUpdateOperationsInput | string
    name?: StringFieldUpdateOperationsInput | string
    role?: StringFieldUpdateOperationsInput | string
  }

  export type SimulationCreateInput = {
    createdAt?: Date | string
    updatedAt?: Date | string
    name: string
    description?: string | null
    status: $Enums.SimulationStatus
    config: JsonNullValueInput | InputJsonValue
    modelType: string
    version: string
    tags?: SimulationCreatetagsInput | string[]
    user: UserCreateNestedOneWithoutSimulationsInput
    BiasDetectionResult?: BiasDetectionResultCreateNestedManyWithoutSimulationInput
    FairnessAssessment?: FairnessAssessmentCreateNestedManyWithoutSimulationInput
    ExplainabilityAnalysis?: ExplainabilityAnalysisCreateNestedManyWithoutSimulationInput
    ComplianceRecord?: ComplianceRecordCreateNestedManyWithoutSimulationInput
    RiskAssessment?: RiskAssessmentCreateNestedManyWithoutSimulationInput
    auditLogs?: AuditLogCreateNestedManyWithoutSimulationInput
  }

  export type SimulationUncheckedCreateInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    name: string
    description?: string | null
    status: $Enums.SimulationStatus
    userId: number
    config: JsonNullValueInput | InputJsonValue
    modelType: string
    version: string
    tags?: SimulationCreatetagsInput | string[]
    BiasDetectionResult?: BiasDetectionResultUncheckedCreateNestedManyWithoutSimulationInput
    FairnessAssessment?: FairnessAssessmentUncheckedCreateNestedManyWithoutSimulationInput
    ExplainabilityAnalysis?: ExplainabilityAnalysisUncheckedCreateNestedManyWithoutSimulationInput
    ComplianceRecord?: ComplianceRecordUncheckedCreateNestedManyWithoutSimulationInput
    RiskAssessment?: RiskAssessmentUncheckedCreateNestedManyWithoutSimulationInput
    auditLogs?: AuditLogUncheckedCreateNestedManyWithoutSimulationInput
  }

  export type SimulationUpdateInput = {
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    name?: StringFieldUpdateOperationsInput | string
    description?: NullableStringFieldUpdateOperationsInput | string | null
    status?: EnumSimulationStatusFieldUpdateOperationsInput | $Enums.SimulationStatus
    config?: JsonNullValueInput | InputJsonValue
    modelType?: StringFieldUpdateOperationsInput | string
    version?: StringFieldUpdateOperationsInput | string
    tags?: SimulationUpdatetagsInput | string[]
    user?: UserUpdateOneRequiredWithoutSimulationsNestedInput
    BiasDetectionResult?: BiasDetectionResultUpdateManyWithoutSimulationNestedInput
    FairnessAssessment?: FairnessAssessmentUpdateManyWithoutSimulationNestedInput
    ExplainabilityAnalysis?: ExplainabilityAnalysisUpdateManyWithoutSimulationNestedInput
    ComplianceRecord?: ComplianceRecordUpdateManyWithoutSimulationNestedInput
    RiskAssessment?: RiskAssessmentUpdateManyWithoutSimulationNestedInput
    auditLogs?: AuditLogUpdateManyWithoutSimulationNestedInput
  }

  export type SimulationUncheckedUpdateInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    name?: StringFieldUpdateOperationsInput | string
    description?: NullableStringFieldUpdateOperationsInput | string | null
    status?: EnumSimulationStatusFieldUpdateOperationsInput | $Enums.SimulationStatus
    userId?: IntFieldUpdateOperationsInput | number
    config?: JsonNullValueInput | InputJsonValue
    modelType?: StringFieldUpdateOperationsInput | string
    version?: StringFieldUpdateOperationsInput | string
    tags?: SimulationUpdatetagsInput | string[]
    BiasDetectionResult?: BiasDetectionResultUncheckedUpdateManyWithoutSimulationNestedInput
    FairnessAssessment?: FairnessAssessmentUncheckedUpdateManyWithoutSimulationNestedInput
    ExplainabilityAnalysis?: ExplainabilityAnalysisUncheckedUpdateManyWithoutSimulationNestedInput
    ComplianceRecord?: ComplianceRecordUncheckedUpdateManyWithoutSimulationNestedInput
    RiskAssessment?: RiskAssessmentUncheckedUpdateManyWithoutSimulationNestedInput
    auditLogs?: AuditLogUncheckedUpdateManyWithoutSimulationNestedInput
  }

  export type SimulationCreateManyInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    name: string
    description?: string | null
    status: $Enums.SimulationStatus
    userId: number
    config: JsonNullValueInput | InputJsonValue
    modelType: string
    version: string
    tags?: SimulationCreatetagsInput | string[]
  }

  export type SimulationUpdateManyMutationInput = {
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    name?: StringFieldUpdateOperationsInput | string
    description?: NullableStringFieldUpdateOperationsInput | string | null
    status?: EnumSimulationStatusFieldUpdateOperationsInput | $Enums.SimulationStatus
    config?: JsonNullValueInput | InputJsonValue
    modelType?: StringFieldUpdateOperationsInput | string
    version?: StringFieldUpdateOperationsInput | string
    tags?: SimulationUpdatetagsInput | string[]
  }

  export type SimulationUncheckedUpdateManyInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    name?: StringFieldUpdateOperationsInput | string
    description?: NullableStringFieldUpdateOperationsInput | string | null
    status?: EnumSimulationStatusFieldUpdateOperationsInput | $Enums.SimulationStatus
    userId?: IntFieldUpdateOperationsInput | number
    config?: JsonNullValueInput | InputJsonValue
    modelType?: StringFieldUpdateOperationsInput | string
    version?: StringFieldUpdateOperationsInput | string
    tags?: SimulationUpdatetagsInput | string[]
  }

  export type BiasDetectionResultCreateInput = {
    createdAt?: Date | string
    updatedAt?: Date | string
    result: JsonNullValueInput | InputJsonValue
    simulation: SimulationCreateNestedOneWithoutBiasDetectionResultInput
  }

  export type BiasDetectionResultUncheckedCreateInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    simulationId: number
    result: JsonNullValueInput | InputJsonValue
  }

  export type BiasDetectionResultUpdateInput = {
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    result?: JsonNullValueInput | InputJsonValue
    simulation?: SimulationUpdateOneRequiredWithoutBiasDetectionResultNestedInput
  }

  export type BiasDetectionResultUncheckedUpdateInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    simulationId?: IntFieldUpdateOperationsInput | number
    result?: JsonNullValueInput | InputJsonValue
  }

  export type BiasDetectionResultCreateManyInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    simulationId: number
    result: JsonNullValueInput | InputJsonValue
  }

  export type BiasDetectionResultUpdateManyMutationInput = {
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    result?: JsonNullValueInput | InputJsonValue
  }

  export type BiasDetectionResultUncheckedUpdateManyInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    simulationId?: IntFieldUpdateOperationsInput | number
    result?: JsonNullValueInput | InputJsonValue
  }

  export type FairnessAssessmentCreateInput = {
    createdAt?: Date | string
    updatedAt?: Date | string
    assessment: JsonNullValueInput | InputJsonValue
    simulation: SimulationCreateNestedOneWithoutFairnessAssessmentInput
  }

  export type FairnessAssessmentUncheckedCreateInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    simulationId: number
    assessment: JsonNullValueInput | InputJsonValue
  }

  export type FairnessAssessmentUpdateInput = {
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    assessment?: JsonNullValueInput | InputJsonValue
    simulation?: SimulationUpdateOneRequiredWithoutFairnessAssessmentNestedInput
  }

  export type FairnessAssessmentUncheckedUpdateInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    simulationId?: IntFieldUpdateOperationsInput | number
    assessment?: JsonNullValueInput | InputJsonValue
  }

  export type FairnessAssessmentCreateManyInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    simulationId: number
    assessment: JsonNullValueInput | InputJsonValue
  }

  export type FairnessAssessmentUpdateManyMutationInput = {
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    assessment?: JsonNullValueInput | InputJsonValue
  }

  export type FairnessAssessmentUncheckedUpdateManyInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    simulationId?: IntFieldUpdateOperationsInput | number
    assessment?: JsonNullValueInput | InputJsonValue
  }

  export type ExplainabilityAnalysisCreateInput = {
    createdAt?: Date | string
    updatedAt?: Date | string
    analysis: JsonNullValueInput | InputJsonValue
    simulation: SimulationCreateNestedOneWithoutExplainabilityAnalysisInput
  }

  export type ExplainabilityAnalysisUncheckedCreateInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    simulationId: number
    analysis: JsonNullValueInput | InputJsonValue
  }

  export type ExplainabilityAnalysisUpdateInput = {
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    analysis?: JsonNullValueInput | InputJsonValue
    simulation?: SimulationUpdateOneRequiredWithoutExplainabilityAnalysisNestedInput
  }

  export type ExplainabilityAnalysisUncheckedUpdateInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    simulationId?: IntFieldUpdateOperationsInput | number
    analysis?: JsonNullValueInput | InputJsonValue
  }

  export type ExplainabilityAnalysisCreateManyInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    simulationId: number
    analysis: JsonNullValueInput | InputJsonValue
  }

  export type ExplainabilityAnalysisUpdateManyMutationInput = {
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    analysis?: JsonNullValueInput | InputJsonValue
  }

  export type ExplainabilityAnalysisUncheckedUpdateManyInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    simulationId?: IntFieldUpdateOperationsInput | number
    analysis?: JsonNullValueInput | InputJsonValue
  }

  export type ComplianceRecordCreateInput = {
    createdAt?: Date | string
    updatedAt?: Date | string
    record: JsonNullValueInput | InputJsonValue
    simulation: SimulationCreateNestedOneWithoutComplianceRecordInput
  }

  export type ComplianceRecordUncheckedCreateInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    simulationId: number
    record: JsonNullValueInput | InputJsonValue
  }

  export type ComplianceRecordUpdateInput = {
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    record?: JsonNullValueInput | InputJsonValue
    simulation?: SimulationUpdateOneRequiredWithoutComplianceRecordNestedInput
  }

  export type ComplianceRecordUncheckedUpdateInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    simulationId?: IntFieldUpdateOperationsInput | number
    record?: JsonNullValueInput | InputJsonValue
  }

  export type ComplianceRecordCreateManyInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    simulationId: number
    record: JsonNullValueInput | InputJsonValue
  }

  export type ComplianceRecordUpdateManyMutationInput = {
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    record?: JsonNullValueInput | InputJsonValue
  }

  export type ComplianceRecordUncheckedUpdateManyInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    simulationId?: IntFieldUpdateOperationsInput | number
    record?: JsonNullValueInput | InputJsonValue
  }

  export type RiskAssessmentCreateInput = {
    createdAt?: Date | string
    updatedAt?: Date | string
    assessment: JsonNullValueInput | InputJsonValue
    simulation: SimulationCreateNestedOneWithoutRiskAssessmentInput
  }

  export type RiskAssessmentUncheckedCreateInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    simulationId: number
    assessment: JsonNullValueInput | InputJsonValue
  }

  export type RiskAssessmentUpdateInput = {
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    assessment?: JsonNullValueInput | InputJsonValue
    simulation?: SimulationUpdateOneRequiredWithoutRiskAssessmentNestedInput
  }

  export type RiskAssessmentUncheckedUpdateInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    simulationId?: IntFieldUpdateOperationsInput | number
    assessment?: JsonNullValueInput | InputJsonValue
  }

  export type RiskAssessmentCreateManyInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    simulationId: number
    assessment: JsonNullValueInput | InputJsonValue
  }

  export type RiskAssessmentUpdateManyMutationInput = {
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    assessment?: JsonNullValueInput | InputJsonValue
  }

  export type RiskAssessmentUncheckedUpdateManyInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    simulationId?: IntFieldUpdateOperationsInput | number
    assessment?: JsonNullValueInput | InputJsonValue
  }

  export type AuditLogCreateInput = {
    createdAt?: Date | string
    action: string
    details: JsonNullValueInput | InputJsonValue
    ipAddress: string
    userAgent: string
    user: UserCreateNestedOneWithoutAuditLogsInput
    simulation?: SimulationCreateNestedOneWithoutAuditLogsInput
  }

  export type AuditLogUncheckedCreateInput = {
    id?: number
    createdAt?: Date | string
    userId: number
    simulationId?: number | null
    action: string
    details: JsonNullValueInput | InputJsonValue
    ipAddress: string
    userAgent: string
  }

  export type AuditLogUpdateInput = {
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    action?: StringFieldUpdateOperationsInput | string
    details?: JsonNullValueInput | InputJsonValue
    ipAddress?: StringFieldUpdateOperationsInput | string
    userAgent?: StringFieldUpdateOperationsInput | string
    user?: UserUpdateOneRequiredWithoutAuditLogsNestedInput
    simulation?: SimulationUpdateOneWithoutAuditLogsNestedInput
  }

  export type AuditLogUncheckedUpdateInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    userId?: IntFieldUpdateOperationsInput | number
    simulationId?: NullableIntFieldUpdateOperationsInput | number | null
    action?: StringFieldUpdateOperationsInput | string
    details?: JsonNullValueInput | InputJsonValue
    ipAddress?: StringFieldUpdateOperationsInput | string
    userAgent?: StringFieldUpdateOperationsInput | string
  }

  export type AuditLogCreateManyInput = {
    id?: number
    createdAt?: Date | string
    userId: number
    simulationId?: number | null
    action: string
    details: JsonNullValueInput | InputJsonValue
    ipAddress: string
    userAgent: string
  }

  export type AuditLogUpdateManyMutationInput = {
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    action?: StringFieldUpdateOperationsInput | string
    details?: JsonNullValueInput | InputJsonValue
    ipAddress?: StringFieldUpdateOperationsInput | string
    userAgent?: StringFieldUpdateOperationsInput | string
  }

  export type AuditLogUncheckedUpdateManyInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    userId?: IntFieldUpdateOperationsInput | number
    simulationId?: NullableIntFieldUpdateOperationsInput | number | null
    action?: StringFieldUpdateOperationsInput | string
    details?: JsonNullValueInput | InputJsonValue
    ipAddress?: StringFieldUpdateOperationsInput | string
    userAgent?: StringFieldUpdateOperationsInput | string
  }

  export type IntFilter<$PrismaModel = never> = {
    equals?: number | IntFieldRefInput<$PrismaModel>
    in?: number[] | ListIntFieldRefInput<$PrismaModel>
    notIn?: number[] | ListIntFieldRefInput<$PrismaModel>
    lt?: number | IntFieldRefInput<$PrismaModel>
    lte?: number | IntFieldRefInput<$PrismaModel>
    gt?: number | IntFieldRefInput<$PrismaModel>
    gte?: number | IntFieldRefInput<$PrismaModel>
    not?: NestedIntFilter<$PrismaModel> | number
  }

  export type DateTimeFilter<$PrismaModel = never> = {
    equals?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    in?: Date[] | string[] | ListDateTimeFieldRefInput<$PrismaModel>
    notIn?: Date[] | string[] | ListDateTimeFieldRefInput<$PrismaModel>
    lt?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    lte?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    gt?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    gte?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    not?: NestedDateTimeFilter<$PrismaModel> | Date | string
  }

  export type StringFilter<$PrismaModel = never> = {
    equals?: string | StringFieldRefInput<$PrismaModel>
    in?: string[] | ListStringFieldRefInput<$PrismaModel>
    notIn?: string[] | ListStringFieldRefInput<$PrismaModel>
    lt?: string | StringFieldRefInput<$PrismaModel>
    lte?: string | StringFieldRefInput<$PrismaModel>
    gt?: string | StringFieldRefInput<$PrismaModel>
    gte?: string | StringFieldRefInput<$PrismaModel>
    contains?: string | StringFieldRefInput<$PrismaModel>
    startsWith?: string | StringFieldRefInput<$PrismaModel>
    endsWith?: string | StringFieldRefInput<$PrismaModel>
    mode?: QueryMode
    not?: NestedStringFilter<$PrismaModel> | string
  }

  export type SimulationListRelationFilter = {
    every?: SimulationWhereInput
    some?: SimulationWhereInput
    none?: SimulationWhereInput
  }

  export type AuditLogListRelationFilter = {
    every?: AuditLogWhereInput
    some?: AuditLogWhereInput
    none?: AuditLogWhereInput
  }

  export type SimulationOrderByRelationAggregateInput = {
    _count?: SortOrder
  }

  export type AuditLogOrderByRelationAggregateInput = {
    _count?: SortOrder
  }

  export type UserCountOrderByAggregateInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    email?: SortOrder
    passwordHash?: SortOrder
    name?: SortOrder
    role?: SortOrder
  }

  export type UserAvgOrderByAggregateInput = {
    id?: SortOrder
  }

  export type UserMaxOrderByAggregateInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    email?: SortOrder
    passwordHash?: SortOrder
    name?: SortOrder
    role?: SortOrder
  }

  export type UserMinOrderByAggregateInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    email?: SortOrder
    passwordHash?: SortOrder
    name?: SortOrder
    role?: SortOrder
  }

  export type UserSumOrderByAggregateInput = {
    id?: SortOrder
  }

  export type IntWithAggregatesFilter<$PrismaModel = never> = {
    equals?: number | IntFieldRefInput<$PrismaModel>
    in?: number[] | ListIntFieldRefInput<$PrismaModel>
    notIn?: number[] | ListIntFieldRefInput<$PrismaModel>
    lt?: number | IntFieldRefInput<$PrismaModel>
    lte?: number | IntFieldRefInput<$PrismaModel>
    gt?: number | IntFieldRefInput<$PrismaModel>
    gte?: number | IntFieldRefInput<$PrismaModel>
    not?: NestedIntWithAggregatesFilter<$PrismaModel> | number
    _count?: NestedIntFilter<$PrismaModel>
    _avg?: NestedFloatFilter<$PrismaModel>
    _sum?: NestedIntFilter<$PrismaModel>
    _min?: NestedIntFilter<$PrismaModel>
    _max?: NestedIntFilter<$PrismaModel>
  }

  export type DateTimeWithAggregatesFilter<$PrismaModel = never> = {
    equals?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    in?: Date[] | string[] | ListDateTimeFieldRefInput<$PrismaModel>
    notIn?: Date[] | string[] | ListDateTimeFieldRefInput<$PrismaModel>
    lt?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    lte?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    gt?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    gte?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    not?: NestedDateTimeWithAggregatesFilter<$PrismaModel> | Date | string
    _count?: NestedIntFilter<$PrismaModel>
    _min?: NestedDateTimeFilter<$PrismaModel>
    _max?: NestedDateTimeFilter<$PrismaModel>
  }

  export type StringWithAggregatesFilter<$PrismaModel = never> = {
    equals?: string | StringFieldRefInput<$PrismaModel>
    in?: string[] | ListStringFieldRefInput<$PrismaModel>
    notIn?: string[] | ListStringFieldRefInput<$PrismaModel>
    lt?: string | StringFieldRefInput<$PrismaModel>
    lte?: string | StringFieldRefInput<$PrismaModel>
    gt?: string | StringFieldRefInput<$PrismaModel>
    gte?: string | StringFieldRefInput<$PrismaModel>
    contains?: string | StringFieldRefInput<$PrismaModel>
    startsWith?: string | StringFieldRefInput<$PrismaModel>
    endsWith?: string | StringFieldRefInput<$PrismaModel>
    mode?: QueryMode
    not?: NestedStringWithAggregatesFilter<$PrismaModel> | string
    _count?: NestedIntFilter<$PrismaModel>
    _min?: NestedStringFilter<$PrismaModel>
    _max?: NestedStringFilter<$PrismaModel>
  }

  export type StringNullableFilter<$PrismaModel = never> = {
    equals?: string | StringFieldRefInput<$PrismaModel> | null
    in?: string[] | ListStringFieldRefInput<$PrismaModel> | null
    notIn?: string[] | ListStringFieldRefInput<$PrismaModel> | null
    lt?: string | StringFieldRefInput<$PrismaModel>
    lte?: string | StringFieldRefInput<$PrismaModel>
    gt?: string | StringFieldRefInput<$PrismaModel>
    gte?: string | StringFieldRefInput<$PrismaModel>
    contains?: string | StringFieldRefInput<$PrismaModel>
    startsWith?: string | StringFieldRefInput<$PrismaModel>
    endsWith?: string | StringFieldRefInput<$PrismaModel>
    mode?: QueryMode
    not?: NestedStringNullableFilter<$PrismaModel> | string | null
  }

  export type EnumSimulationStatusFilter<$PrismaModel = never> = {
    equals?: $Enums.SimulationStatus | EnumSimulationStatusFieldRefInput<$PrismaModel>
    in?: $Enums.SimulationStatus[] | ListEnumSimulationStatusFieldRefInput<$PrismaModel>
    notIn?: $Enums.SimulationStatus[] | ListEnumSimulationStatusFieldRefInput<$PrismaModel>
    not?: NestedEnumSimulationStatusFilter<$PrismaModel> | $Enums.SimulationStatus
  }
  export type JsonFilter<$PrismaModel = never> =
    | PatchUndefined<
        Either<Required<JsonFilterBase<$PrismaModel>>, Exclude<keyof Required<JsonFilterBase<$PrismaModel>>, 'path'>>,
        Required<JsonFilterBase<$PrismaModel>>
      >
    | OptionalFlat<Omit<Required<JsonFilterBase<$PrismaModel>>, 'path'>>

  export type JsonFilterBase<$PrismaModel = never> = {
    equals?: InputJsonValue | JsonFieldRefInput<$PrismaModel> | JsonNullValueFilter
    path?: string[]
    mode?: QueryMode | EnumQueryModeFieldRefInput<$PrismaModel>
    string_contains?: string | StringFieldRefInput<$PrismaModel>
    string_starts_with?: string | StringFieldRefInput<$PrismaModel>
    string_ends_with?: string | StringFieldRefInput<$PrismaModel>
    array_starts_with?: InputJsonValue | JsonFieldRefInput<$PrismaModel> | null
    array_ends_with?: InputJsonValue | JsonFieldRefInput<$PrismaModel> | null
    array_contains?: InputJsonValue | JsonFieldRefInput<$PrismaModel> | null
    lt?: InputJsonValue | JsonFieldRefInput<$PrismaModel>
    lte?: InputJsonValue | JsonFieldRefInput<$PrismaModel>
    gt?: InputJsonValue | JsonFieldRefInput<$PrismaModel>
    gte?: InputJsonValue | JsonFieldRefInput<$PrismaModel>
    not?: InputJsonValue | JsonFieldRefInput<$PrismaModel> | JsonNullValueFilter
  }

  export type StringNullableListFilter<$PrismaModel = never> = {
    equals?: string[] | ListStringFieldRefInput<$PrismaModel> | null
    has?: string | StringFieldRefInput<$PrismaModel> | null
    hasEvery?: string[] | ListStringFieldRefInput<$PrismaModel>
    hasSome?: string[] | ListStringFieldRefInput<$PrismaModel>
    isEmpty?: boolean
  }

  export type UserScalarRelationFilter = {
    is?: UserWhereInput
    isNot?: UserWhereInput
  }

  export type BiasDetectionResultListRelationFilter = {
    every?: BiasDetectionResultWhereInput
    some?: BiasDetectionResultWhereInput
    none?: BiasDetectionResultWhereInput
  }

  export type FairnessAssessmentListRelationFilter = {
    every?: FairnessAssessmentWhereInput
    some?: FairnessAssessmentWhereInput
    none?: FairnessAssessmentWhereInput
  }

  export type ExplainabilityAnalysisListRelationFilter = {
    every?: ExplainabilityAnalysisWhereInput
    some?: ExplainabilityAnalysisWhereInput
    none?: ExplainabilityAnalysisWhereInput
  }

  export type ComplianceRecordListRelationFilter = {
    every?: ComplianceRecordWhereInput
    some?: ComplianceRecordWhereInput
    none?: ComplianceRecordWhereInput
  }

  export type RiskAssessmentListRelationFilter = {
    every?: RiskAssessmentWhereInput
    some?: RiskAssessmentWhereInput
    none?: RiskAssessmentWhereInput
  }

  export type SortOrderInput = {
    sort: SortOrder
    nulls?: NullsOrder
  }

  export type BiasDetectionResultOrderByRelationAggregateInput = {
    _count?: SortOrder
  }

  export type FairnessAssessmentOrderByRelationAggregateInput = {
    _count?: SortOrder
  }

  export type ExplainabilityAnalysisOrderByRelationAggregateInput = {
    _count?: SortOrder
  }

  export type ComplianceRecordOrderByRelationAggregateInput = {
    _count?: SortOrder
  }

  export type RiskAssessmentOrderByRelationAggregateInput = {
    _count?: SortOrder
  }

  export type SimulationCountOrderByAggregateInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    name?: SortOrder
    description?: SortOrder
    status?: SortOrder
    userId?: SortOrder
    config?: SortOrder
    modelType?: SortOrder
    version?: SortOrder
    tags?: SortOrder
  }

  export type SimulationAvgOrderByAggregateInput = {
    id?: SortOrder
    userId?: SortOrder
  }

  export type SimulationMaxOrderByAggregateInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    name?: SortOrder
    description?: SortOrder
    status?: SortOrder
    userId?: SortOrder
    modelType?: SortOrder
    version?: SortOrder
  }

  export type SimulationMinOrderByAggregateInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    name?: SortOrder
    description?: SortOrder
    status?: SortOrder
    userId?: SortOrder
    modelType?: SortOrder
    version?: SortOrder
  }

  export type SimulationSumOrderByAggregateInput = {
    id?: SortOrder
    userId?: SortOrder
  }

  export type StringNullableWithAggregatesFilter<$PrismaModel = never> = {
    equals?: string | StringFieldRefInput<$PrismaModel> | null
    in?: string[] | ListStringFieldRefInput<$PrismaModel> | null
    notIn?: string[] | ListStringFieldRefInput<$PrismaModel> | null
    lt?: string | StringFieldRefInput<$PrismaModel>
    lte?: string | StringFieldRefInput<$PrismaModel>
    gt?: string | StringFieldRefInput<$PrismaModel>
    gte?: string | StringFieldRefInput<$PrismaModel>
    contains?: string | StringFieldRefInput<$PrismaModel>
    startsWith?: string | StringFieldRefInput<$PrismaModel>
    endsWith?: string | StringFieldRefInput<$PrismaModel>
    mode?: QueryMode
    not?: NestedStringNullableWithAggregatesFilter<$PrismaModel> | string | null
    _count?: NestedIntNullableFilter<$PrismaModel>
    _min?: NestedStringNullableFilter<$PrismaModel>
    _max?: NestedStringNullableFilter<$PrismaModel>
  }

  export type EnumSimulationStatusWithAggregatesFilter<$PrismaModel = never> = {
    equals?: $Enums.SimulationStatus | EnumSimulationStatusFieldRefInput<$PrismaModel>
    in?: $Enums.SimulationStatus[] | ListEnumSimulationStatusFieldRefInput<$PrismaModel>
    notIn?: $Enums.SimulationStatus[] | ListEnumSimulationStatusFieldRefInput<$PrismaModel>
    not?: NestedEnumSimulationStatusWithAggregatesFilter<$PrismaModel> | $Enums.SimulationStatus
    _count?: NestedIntFilter<$PrismaModel>
    _min?: NestedEnumSimulationStatusFilter<$PrismaModel>
    _max?: NestedEnumSimulationStatusFilter<$PrismaModel>
  }
  export type JsonWithAggregatesFilter<$PrismaModel = never> =
    | PatchUndefined<
        Either<Required<JsonWithAggregatesFilterBase<$PrismaModel>>, Exclude<keyof Required<JsonWithAggregatesFilterBase<$PrismaModel>>, 'path'>>,
        Required<JsonWithAggregatesFilterBase<$PrismaModel>>
      >
    | OptionalFlat<Omit<Required<JsonWithAggregatesFilterBase<$PrismaModel>>, 'path'>>

  export type JsonWithAggregatesFilterBase<$PrismaModel = never> = {
    equals?: InputJsonValue | JsonFieldRefInput<$PrismaModel> | JsonNullValueFilter
    path?: string[]
    mode?: QueryMode | EnumQueryModeFieldRefInput<$PrismaModel>
    string_contains?: string | StringFieldRefInput<$PrismaModel>
    string_starts_with?: string | StringFieldRefInput<$PrismaModel>
    string_ends_with?: string | StringFieldRefInput<$PrismaModel>
    array_starts_with?: InputJsonValue | JsonFieldRefInput<$PrismaModel> | null
    array_ends_with?: InputJsonValue | JsonFieldRefInput<$PrismaModel> | null
    array_contains?: InputJsonValue | JsonFieldRefInput<$PrismaModel> | null
    lt?: InputJsonValue | JsonFieldRefInput<$PrismaModel>
    lte?: InputJsonValue | JsonFieldRefInput<$PrismaModel>
    gt?: InputJsonValue | JsonFieldRefInput<$PrismaModel>
    gte?: InputJsonValue | JsonFieldRefInput<$PrismaModel>
    not?: InputJsonValue | JsonFieldRefInput<$PrismaModel> | JsonNullValueFilter
    _count?: NestedIntFilter<$PrismaModel>
    _min?: NestedJsonFilter<$PrismaModel>
    _max?: NestedJsonFilter<$PrismaModel>
  }

  export type SimulationScalarRelationFilter = {
    is?: SimulationWhereInput
    isNot?: SimulationWhereInput
  }

  export type BiasDetectionResultCountOrderByAggregateInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    simulationId?: SortOrder
    result?: SortOrder
  }

  export type BiasDetectionResultAvgOrderByAggregateInput = {
    id?: SortOrder
    simulationId?: SortOrder
  }

  export type BiasDetectionResultMaxOrderByAggregateInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    simulationId?: SortOrder
  }

  export type BiasDetectionResultMinOrderByAggregateInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    simulationId?: SortOrder
  }

  export type BiasDetectionResultSumOrderByAggregateInput = {
    id?: SortOrder
    simulationId?: SortOrder
  }

  export type FairnessAssessmentCountOrderByAggregateInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    simulationId?: SortOrder
    assessment?: SortOrder
  }

  export type FairnessAssessmentAvgOrderByAggregateInput = {
    id?: SortOrder
    simulationId?: SortOrder
  }

  export type FairnessAssessmentMaxOrderByAggregateInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    simulationId?: SortOrder
  }

  export type FairnessAssessmentMinOrderByAggregateInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    simulationId?: SortOrder
  }

  export type FairnessAssessmentSumOrderByAggregateInput = {
    id?: SortOrder
    simulationId?: SortOrder
  }

  export type ExplainabilityAnalysisCountOrderByAggregateInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    simulationId?: SortOrder
    analysis?: SortOrder
  }

  export type ExplainabilityAnalysisAvgOrderByAggregateInput = {
    id?: SortOrder
    simulationId?: SortOrder
  }

  export type ExplainabilityAnalysisMaxOrderByAggregateInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    simulationId?: SortOrder
  }

  export type ExplainabilityAnalysisMinOrderByAggregateInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    simulationId?: SortOrder
  }

  export type ExplainabilityAnalysisSumOrderByAggregateInput = {
    id?: SortOrder
    simulationId?: SortOrder
  }

  export type ComplianceRecordCountOrderByAggregateInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    simulationId?: SortOrder
    record?: SortOrder
  }

  export type ComplianceRecordAvgOrderByAggregateInput = {
    id?: SortOrder
    simulationId?: SortOrder
  }

  export type ComplianceRecordMaxOrderByAggregateInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    simulationId?: SortOrder
  }

  export type ComplianceRecordMinOrderByAggregateInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    simulationId?: SortOrder
  }

  export type ComplianceRecordSumOrderByAggregateInput = {
    id?: SortOrder
    simulationId?: SortOrder
  }

  export type RiskAssessmentCountOrderByAggregateInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    simulationId?: SortOrder
    assessment?: SortOrder
  }

  export type RiskAssessmentAvgOrderByAggregateInput = {
    id?: SortOrder
    simulationId?: SortOrder
  }

  export type RiskAssessmentMaxOrderByAggregateInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    simulationId?: SortOrder
  }

  export type RiskAssessmentMinOrderByAggregateInput = {
    id?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    simulationId?: SortOrder
  }

  export type RiskAssessmentSumOrderByAggregateInput = {
    id?: SortOrder
    simulationId?: SortOrder
  }

  export type IntNullableFilter<$PrismaModel = never> = {
    equals?: number | IntFieldRefInput<$PrismaModel> | null
    in?: number[] | ListIntFieldRefInput<$PrismaModel> | null
    notIn?: number[] | ListIntFieldRefInput<$PrismaModel> | null
    lt?: number | IntFieldRefInput<$PrismaModel>
    lte?: number | IntFieldRefInput<$PrismaModel>
    gt?: number | IntFieldRefInput<$PrismaModel>
    gte?: number | IntFieldRefInput<$PrismaModel>
    not?: NestedIntNullableFilter<$PrismaModel> | number | null
  }

  export type SimulationNullableScalarRelationFilter = {
    is?: SimulationWhereInput | null
    isNot?: SimulationWhereInput | null
  }

  export type AuditLogCountOrderByAggregateInput = {
    id?: SortOrder
    createdAt?: SortOrder
    userId?: SortOrder
    simulationId?: SortOrder
    action?: SortOrder
    details?: SortOrder
    ipAddress?: SortOrder
    userAgent?: SortOrder
  }

  export type AuditLogAvgOrderByAggregateInput = {
    id?: SortOrder
    userId?: SortOrder
    simulationId?: SortOrder
  }

  export type AuditLogMaxOrderByAggregateInput = {
    id?: SortOrder
    createdAt?: SortOrder
    userId?: SortOrder
    simulationId?: SortOrder
    action?: SortOrder
    ipAddress?: SortOrder
    userAgent?: SortOrder
  }

  export type AuditLogMinOrderByAggregateInput = {
    id?: SortOrder
    createdAt?: SortOrder
    userId?: SortOrder
    simulationId?: SortOrder
    action?: SortOrder
    ipAddress?: SortOrder
    userAgent?: SortOrder
  }

  export type AuditLogSumOrderByAggregateInput = {
    id?: SortOrder
    userId?: SortOrder
    simulationId?: SortOrder
  }

  export type IntNullableWithAggregatesFilter<$PrismaModel = never> = {
    equals?: number | IntFieldRefInput<$PrismaModel> | null
    in?: number[] | ListIntFieldRefInput<$PrismaModel> | null
    notIn?: number[] | ListIntFieldRefInput<$PrismaModel> | null
    lt?: number | IntFieldRefInput<$PrismaModel>
    lte?: number | IntFieldRefInput<$PrismaModel>
    gt?: number | IntFieldRefInput<$PrismaModel>
    gte?: number | IntFieldRefInput<$PrismaModel>
    not?: NestedIntNullableWithAggregatesFilter<$PrismaModel> | number | null
    _count?: NestedIntNullableFilter<$PrismaModel>
    _avg?: NestedFloatNullableFilter<$PrismaModel>
    _sum?: NestedIntNullableFilter<$PrismaModel>
    _min?: NestedIntNullableFilter<$PrismaModel>
    _max?: NestedIntNullableFilter<$PrismaModel>
  }

  export type SimulationCreateNestedManyWithoutUserInput = {
    create?: XOR<SimulationCreateWithoutUserInput, SimulationUncheckedCreateWithoutUserInput> | SimulationCreateWithoutUserInput[] | SimulationUncheckedCreateWithoutUserInput[]
    connectOrCreate?: SimulationCreateOrConnectWithoutUserInput | SimulationCreateOrConnectWithoutUserInput[]
    createMany?: SimulationCreateManyUserInputEnvelope
    connect?: SimulationWhereUniqueInput | SimulationWhereUniqueInput[]
  }

  export type AuditLogCreateNestedManyWithoutUserInput = {
    create?: XOR<AuditLogCreateWithoutUserInput, AuditLogUncheckedCreateWithoutUserInput> | AuditLogCreateWithoutUserInput[] | AuditLogUncheckedCreateWithoutUserInput[]
    connectOrCreate?: AuditLogCreateOrConnectWithoutUserInput | AuditLogCreateOrConnectWithoutUserInput[]
    createMany?: AuditLogCreateManyUserInputEnvelope
    connect?: AuditLogWhereUniqueInput | AuditLogWhereUniqueInput[]
  }

  export type SimulationUncheckedCreateNestedManyWithoutUserInput = {
    create?: XOR<SimulationCreateWithoutUserInput, SimulationUncheckedCreateWithoutUserInput> | SimulationCreateWithoutUserInput[] | SimulationUncheckedCreateWithoutUserInput[]
    connectOrCreate?: SimulationCreateOrConnectWithoutUserInput | SimulationCreateOrConnectWithoutUserInput[]
    createMany?: SimulationCreateManyUserInputEnvelope
    connect?: SimulationWhereUniqueInput | SimulationWhereUniqueInput[]
  }

  export type AuditLogUncheckedCreateNestedManyWithoutUserInput = {
    create?: XOR<AuditLogCreateWithoutUserInput, AuditLogUncheckedCreateWithoutUserInput> | AuditLogCreateWithoutUserInput[] | AuditLogUncheckedCreateWithoutUserInput[]
    connectOrCreate?: AuditLogCreateOrConnectWithoutUserInput | AuditLogCreateOrConnectWithoutUserInput[]
    createMany?: AuditLogCreateManyUserInputEnvelope
    connect?: AuditLogWhereUniqueInput | AuditLogWhereUniqueInput[]
  }

  export type DateTimeFieldUpdateOperationsInput = {
    set?: Date | string
  }

  export type StringFieldUpdateOperationsInput = {
    set?: string
  }

  export type SimulationUpdateManyWithoutUserNestedInput = {
    create?: XOR<SimulationCreateWithoutUserInput, SimulationUncheckedCreateWithoutUserInput> | SimulationCreateWithoutUserInput[] | SimulationUncheckedCreateWithoutUserInput[]
    connectOrCreate?: SimulationCreateOrConnectWithoutUserInput | SimulationCreateOrConnectWithoutUserInput[]
    upsert?: SimulationUpsertWithWhereUniqueWithoutUserInput | SimulationUpsertWithWhereUniqueWithoutUserInput[]
    createMany?: SimulationCreateManyUserInputEnvelope
    set?: SimulationWhereUniqueInput | SimulationWhereUniqueInput[]
    disconnect?: SimulationWhereUniqueInput | SimulationWhereUniqueInput[]
    delete?: SimulationWhereUniqueInput | SimulationWhereUniqueInput[]
    connect?: SimulationWhereUniqueInput | SimulationWhereUniqueInput[]
    update?: SimulationUpdateWithWhereUniqueWithoutUserInput | SimulationUpdateWithWhereUniqueWithoutUserInput[]
    updateMany?: SimulationUpdateManyWithWhereWithoutUserInput | SimulationUpdateManyWithWhereWithoutUserInput[]
    deleteMany?: SimulationScalarWhereInput | SimulationScalarWhereInput[]
  }

  export type AuditLogUpdateManyWithoutUserNestedInput = {
    create?: XOR<AuditLogCreateWithoutUserInput, AuditLogUncheckedCreateWithoutUserInput> | AuditLogCreateWithoutUserInput[] | AuditLogUncheckedCreateWithoutUserInput[]
    connectOrCreate?: AuditLogCreateOrConnectWithoutUserInput | AuditLogCreateOrConnectWithoutUserInput[]
    upsert?: AuditLogUpsertWithWhereUniqueWithoutUserInput | AuditLogUpsertWithWhereUniqueWithoutUserInput[]
    createMany?: AuditLogCreateManyUserInputEnvelope
    set?: AuditLogWhereUniqueInput | AuditLogWhereUniqueInput[]
    disconnect?: AuditLogWhereUniqueInput | AuditLogWhereUniqueInput[]
    delete?: AuditLogWhereUniqueInput | AuditLogWhereUniqueInput[]
    connect?: AuditLogWhereUniqueInput | AuditLogWhereUniqueInput[]
    update?: AuditLogUpdateWithWhereUniqueWithoutUserInput | AuditLogUpdateWithWhereUniqueWithoutUserInput[]
    updateMany?: AuditLogUpdateManyWithWhereWithoutUserInput | AuditLogUpdateManyWithWhereWithoutUserInput[]
    deleteMany?: AuditLogScalarWhereInput | AuditLogScalarWhereInput[]
  }

  export type IntFieldUpdateOperationsInput = {
    set?: number
    increment?: number
    decrement?: number
    multiply?: number
    divide?: number
  }

  export type SimulationUncheckedUpdateManyWithoutUserNestedInput = {
    create?: XOR<SimulationCreateWithoutUserInput, SimulationUncheckedCreateWithoutUserInput> | SimulationCreateWithoutUserInput[] | SimulationUncheckedCreateWithoutUserInput[]
    connectOrCreate?: SimulationCreateOrConnectWithoutUserInput | SimulationCreateOrConnectWithoutUserInput[]
    upsert?: SimulationUpsertWithWhereUniqueWithoutUserInput | SimulationUpsertWithWhereUniqueWithoutUserInput[]
    createMany?: SimulationCreateManyUserInputEnvelope
    set?: SimulationWhereUniqueInput | SimulationWhereUniqueInput[]
    disconnect?: SimulationWhereUniqueInput | SimulationWhereUniqueInput[]
    delete?: SimulationWhereUniqueInput | SimulationWhereUniqueInput[]
    connect?: SimulationWhereUniqueInput | SimulationWhereUniqueInput[]
    update?: SimulationUpdateWithWhereUniqueWithoutUserInput | SimulationUpdateWithWhereUniqueWithoutUserInput[]
    updateMany?: SimulationUpdateManyWithWhereWithoutUserInput | SimulationUpdateManyWithWhereWithoutUserInput[]
    deleteMany?: SimulationScalarWhereInput | SimulationScalarWhereInput[]
  }

  export type AuditLogUncheckedUpdateManyWithoutUserNestedInput = {
    create?: XOR<AuditLogCreateWithoutUserInput, AuditLogUncheckedCreateWithoutUserInput> | AuditLogCreateWithoutUserInput[] | AuditLogUncheckedCreateWithoutUserInput[]
    connectOrCreate?: AuditLogCreateOrConnectWithoutUserInput | AuditLogCreateOrConnectWithoutUserInput[]
    upsert?: AuditLogUpsertWithWhereUniqueWithoutUserInput | AuditLogUpsertWithWhereUniqueWithoutUserInput[]
    createMany?: AuditLogCreateManyUserInputEnvelope
    set?: AuditLogWhereUniqueInput | AuditLogWhereUniqueInput[]
    disconnect?: AuditLogWhereUniqueInput | AuditLogWhereUniqueInput[]
    delete?: AuditLogWhereUniqueInput | AuditLogWhereUniqueInput[]
    connect?: AuditLogWhereUniqueInput | AuditLogWhereUniqueInput[]
    update?: AuditLogUpdateWithWhereUniqueWithoutUserInput | AuditLogUpdateWithWhereUniqueWithoutUserInput[]
    updateMany?: AuditLogUpdateManyWithWhereWithoutUserInput | AuditLogUpdateManyWithWhereWithoutUserInput[]
    deleteMany?: AuditLogScalarWhereInput | AuditLogScalarWhereInput[]
  }

  export type SimulationCreatetagsInput = {
    set: string[]
  }

  export type UserCreateNestedOneWithoutSimulationsInput = {
    create?: XOR<UserCreateWithoutSimulationsInput, UserUncheckedCreateWithoutSimulationsInput>
    connectOrCreate?: UserCreateOrConnectWithoutSimulationsInput
    connect?: UserWhereUniqueInput
  }

  export type BiasDetectionResultCreateNestedManyWithoutSimulationInput = {
    create?: XOR<BiasDetectionResultCreateWithoutSimulationInput, BiasDetectionResultUncheckedCreateWithoutSimulationInput> | BiasDetectionResultCreateWithoutSimulationInput[] | BiasDetectionResultUncheckedCreateWithoutSimulationInput[]
    connectOrCreate?: BiasDetectionResultCreateOrConnectWithoutSimulationInput | BiasDetectionResultCreateOrConnectWithoutSimulationInput[]
    createMany?: BiasDetectionResultCreateManySimulationInputEnvelope
    connect?: BiasDetectionResultWhereUniqueInput | BiasDetectionResultWhereUniqueInput[]
  }

  export type FairnessAssessmentCreateNestedManyWithoutSimulationInput = {
    create?: XOR<FairnessAssessmentCreateWithoutSimulationInput, FairnessAssessmentUncheckedCreateWithoutSimulationInput> | FairnessAssessmentCreateWithoutSimulationInput[] | FairnessAssessmentUncheckedCreateWithoutSimulationInput[]
    connectOrCreate?: FairnessAssessmentCreateOrConnectWithoutSimulationInput | FairnessAssessmentCreateOrConnectWithoutSimulationInput[]
    createMany?: FairnessAssessmentCreateManySimulationInputEnvelope
    connect?: FairnessAssessmentWhereUniqueInput | FairnessAssessmentWhereUniqueInput[]
  }

  export type ExplainabilityAnalysisCreateNestedManyWithoutSimulationInput = {
    create?: XOR<ExplainabilityAnalysisCreateWithoutSimulationInput, ExplainabilityAnalysisUncheckedCreateWithoutSimulationInput> | ExplainabilityAnalysisCreateWithoutSimulationInput[] | ExplainabilityAnalysisUncheckedCreateWithoutSimulationInput[]
    connectOrCreate?: ExplainabilityAnalysisCreateOrConnectWithoutSimulationInput | ExplainabilityAnalysisCreateOrConnectWithoutSimulationInput[]
    createMany?: ExplainabilityAnalysisCreateManySimulationInputEnvelope
    connect?: ExplainabilityAnalysisWhereUniqueInput | ExplainabilityAnalysisWhereUniqueInput[]
  }

  export type ComplianceRecordCreateNestedManyWithoutSimulationInput = {
    create?: XOR<ComplianceRecordCreateWithoutSimulationInput, ComplianceRecordUncheckedCreateWithoutSimulationInput> | ComplianceRecordCreateWithoutSimulationInput[] | ComplianceRecordUncheckedCreateWithoutSimulationInput[]
    connectOrCreate?: ComplianceRecordCreateOrConnectWithoutSimulationInput | ComplianceRecordCreateOrConnectWithoutSimulationInput[]
    createMany?: ComplianceRecordCreateManySimulationInputEnvelope
    connect?: ComplianceRecordWhereUniqueInput | ComplianceRecordWhereUniqueInput[]
  }

  export type RiskAssessmentCreateNestedManyWithoutSimulationInput = {
    create?: XOR<RiskAssessmentCreateWithoutSimulationInput, RiskAssessmentUncheckedCreateWithoutSimulationInput> | RiskAssessmentCreateWithoutSimulationInput[] | RiskAssessmentUncheckedCreateWithoutSimulationInput[]
    connectOrCreate?: RiskAssessmentCreateOrConnectWithoutSimulationInput | RiskAssessmentCreateOrConnectWithoutSimulationInput[]
    createMany?: RiskAssessmentCreateManySimulationInputEnvelope
    connect?: RiskAssessmentWhereUniqueInput | RiskAssessmentWhereUniqueInput[]
  }

  export type AuditLogCreateNestedManyWithoutSimulationInput = {
    create?: XOR<AuditLogCreateWithoutSimulationInput, AuditLogUncheckedCreateWithoutSimulationInput> | AuditLogCreateWithoutSimulationInput[] | AuditLogUncheckedCreateWithoutSimulationInput[]
    connectOrCreate?: AuditLogCreateOrConnectWithoutSimulationInput | AuditLogCreateOrConnectWithoutSimulationInput[]
    createMany?: AuditLogCreateManySimulationInputEnvelope
    connect?: AuditLogWhereUniqueInput | AuditLogWhereUniqueInput[]
  }

  export type BiasDetectionResultUncheckedCreateNestedManyWithoutSimulationInput = {
    create?: XOR<BiasDetectionResultCreateWithoutSimulationInput, BiasDetectionResultUncheckedCreateWithoutSimulationInput> | BiasDetectionResultCreateWithoutSimulationInput[] | BiasDetectionResultUncheckedCreateWithoutSimulationInput[]
    connectOrCreate?: BiasDetectionResultCreateOrConnectWithoutSimulationInput | BiasDetectionResultCreateOrConnectWithoutSimulationInput[]
    createMany?: BiasDetectionResultCreateManySimulationInputEnvelope
    connect?: BiasDetectionResultWhereUniqueInput | BiasDetectionResultWhereUniqueInput[]
  }

  export type FairnessAssessmentUncheckedCreateNestedManyWithoutSimulationInput = {
    create?: XOR<FairnessAssessmentCreateWithoutSimulationInput, FairnessAssessmentUncheckedCreateWithoutSimulationInput> | FairnessAssessmentCreateWithoutSimulationInput[] | FairnessAssessmentUncheckedCreateWithoutSimulationInput[]
    connectOrCreate?: FairnessAssessmentCreateOrConnectWithoutSimulationInput | FairnessAssessmentCreateOrConnectWithoutSimulationInput[]
    createMany?: FairnessAssessmentCreateManySimulationInputEnvelope
    connect?: FairnessAssessmentWhereUniqueInput | FairnessAssessmentWhereUniqueInput[]
  }

  export type ExplainabilityAnalysisUncheckedCreateNestedManyWithoutSimulationInput = {
    create?: XOR<ExplainabilityAnalysisCreateWithoutSimulationInput, ExplainabilityAnalysisUncheckedCreateWithoutSimulationInput> | ExplainabilityAnalysisCreateWithoutSimulationInput[] | ExplainabilityAnalysisUncheckedCreateWithoutSimulationInput[]
    connectOrCreate?: ExplainabilityAnalysisCreateOrConnectWithoutSimulationInput | ExplainabilityAnalysisCreateOrConnectWithoutSimulationInput[]
    createMany?: ExplainabilityAnalysisCreateManySimulationInputEnvelope
    connect?: ExplainabilityAnalysisWhereUniqueInput | ExplainabilityAnalysisWhereUniqueInput[]
  }

  export type ComplianceRecordUncheckedCreateNestedManyWithoutSimulationInput = {
    create?: XOR<ComplianceRecordCreateWithoutSimulationInput, ComplianceRecordUncheckedCreateWithoutSimulationInput> | ComplianceRecordCreateWithoutSimulationInput[] | ComplianceRecordUncheckedCreateWithoutSimulationInput[]
    connectOrCreate?: ComplianceRecordCreateOrConnectWithoutSimulationInput | ComplianceRecordCreateOrConnectWithoutSimulationInput[]
    createMany?: ComplianceRecordCreateManySimulationInputEnvelope
    connect?: ComplianceRecordWhereUniqueInput | ComplianceRecordWhereUniqueInput[]
  }

  export type RiskAssessmentUncheckedCreateNestedManyWithoutSimulationInput = {
    create?: XOR<RiskAssessmentCreateWithoutSimulationInput, RiskAssessmentUncheckedCreateWithoutSimulationInput> | RiskAssessmentCreateWithoutSimulationInput[] | RiskAssessmentUncheckedCreateWithoutSimulationInput[]
    connectOrCreate?: RiskAssessmentCreateOrConnectWithoutSimulationInput | RiskAssessmentCreateOrConnectWithoutSimulationInput[]
    createMany?: RiskAssessmentCreateManySimulationInputEnvelope
    connect?: RiskAssessmentWhereUniqueInput | RiskAssessmentWhereUniqueInput[]
  }

  export type AuditLogUncheckedCreateNestedManyWithoutSimulationInput = {
    create?: XOR<AuditLogCreateWithoutSimulationInput, AuditLogUncheckedCreateWithoutSimulationInput> | AuditLogCreateWithoutSimulationInput[] | AuditLogUncheckedCreateWithoutSimulationInput[]
    connectOrCreate?: AuditLogCreateOrConnectWithoutSimulationInput | AuditLogCreateOrConnectWithoutSimulationInput[]
    createMany?: AuditLogCreateManySimulationInputEnvelope
    connect?: AuditLogWhereUniqueInput | AuditLogWhereUniqueInput[]
  }

  export type NullableStringFieldUpdateOperationsInput = {
    set?: string | null
  }

  export type EnumSimulationStatusFieldUpdateOperationsInput = {
    set?: $Enums.SimulationStatus
  }

  export type SimulationUpdatetagsInput = {
    set?: string[]
    push?: string | string[]
  }

  export type UserUpdateOneRequiredWithoutSimulationsNestedInput = {
    create?: XOR<UserCreateWithoutSimulationsInput, UserUncheckedCreateWithoutSimulationsInput>
    connectOrCreate?: UserCreateOrConnectWithoutSimulationsInput
    upsert?: UserUpsertWithoutSimulationsInput
    connect?: UserWhereUniqueInput
    update?: XOR<XOR<UserUpdateToOneWithWhereWithoutSimulationsInput, UserUpdateWithoutSimulationsInput>, UserUncheckedUpdateWithoutSimulationsInput>
  }

  export type BiasDetectionResultUpdateManyWithoutSimulationNestedInput = {
    create?: XOR<BiasDetectionResultCreateWithoutSimulationInput, BiasDetectionResultUncheckedCreateWithoutSimulationInput> | BiasDetectionResultCreateWithoutSimulationInput[] | BiasDetectionResultUncheckedCreateWithoutSimulationInput[]
    connectOrCreate?: BiasDetectionResultCreateOrConnectWithoutSimulationInput | BiasDetectionResultCreateOrConnectWithoutSimulationInput[]
    upsert?: BiasDetectionResultUpsertWithWhereUniqueWithoutSimulationInput | BiasDetectionResultUpsertWithWhereUniqueWithoutSimulationInput[]
    createMany?: BiasDetectionResultCreateManySimulationInputEnvelope
    set?: BiasDetectionResultWhereUniqueInput | BiasDetectionResultWhereUniqueInput[]
    disconnect?: BiasDetectionResultWhereUniqueInput | BiasDetectionResultWhereUniqueInput[]
    delete?: BiasDetectionResultWhereUniqueInput | BiasDetectionResultWhereUniqueInput[]
    connect?: BiasDetectionResultWhereUniqueInput | BiasDetectionResultWhereUniqueInput[]
    update?: BiasDetectionResultUpdateWithWhereUniqueWithoutSimulationInput | BiasDetectionResultUpdateWithWhereUniqueWithoutSimulationInput[]
    updateMany?: BiasDetectionResultUpdateManyWithWhereWithoutSimulationInput | BiasDetectionResultUpdateManyWithWhereWithoutSimulationInput[]
    deleteMany?: BiasDetectionResultScalarWhereInput | BiasDetectionResultScalarWhereInput[]
  }

  export type FairnessAssessmentUpdateManyWithoutSimulationNestedInput = {
    create?: XOR<FairnessAssessmentCreateWithoutSimulationInput, FairnessAssessmentUncheckedCreateWithoutSimulationInput> | FairnessAssessmentCreateWithoutSimulationInput[] | FairnessAssessmentUncheckedCreateWithoutSimulationInput[]
    connectOrCreate?: FairnessAssessmentCreateOrConnectWithoutSimulationInput | FairnessAssessmentCreateOrConnectWithoutSimulationInput[]
    upsert?: FairnessAssessmentUpsertWithWhereUniqueWithoutSimulationInput | FairnessAssessmentUpsertWithWhereUniqueWithoutSimulationInput[]
    createMany?: FairnessAssessmentCreateManySimulationInputEnvelope
    set?: FairnessAssessmentWhereUniqueInput | FairnessAssessmentWhereUniqueInput[]
    disconnect?: FairnessAssessmentWhereUniqueInput | FairnessAssessmentWhereUniqueInput[]
    delete?: FairnessAssessmentWhereUniqueInput | FairnessAssessmentWhereUniqueInput[]
    connect?: FairnessAssessmentWhereUniqueInput | FairnessAssessmentWhereUniqueInput[]
    update?: FairnessAssessmentUpdateWithWhereUniqueWithoutSimulationInput | FairnessAssessmentUpdateWithWhereUniqueWithoutSimulationInput[]
    updateMany?: FairnessAssessmentUpdateManyWithWhereWithoutSimulationInput | FairnessAssessmentUpdateManyWithWhereWithoutSimulationInput[]
    deleteMany?: FairnessAssessmentScalarWhereInput | FairnessAssessmentScalarWhereInput[]
  }

  export type ExplainabilityAnalysisUpdateManyWithoutSimulationNestedInput = {
    create?: XOR<ExplainabilityAnalysisCreateWithoutSimulationInput, ExplainabilityAnalysisUncheckedCreateWithoutSimulationInput> | ExplainabilityAnalysisCreateWithoutSimulationInput[] | ExplainabilityAnalysisUncheckedCreateWithoutSimulationInput[]
    connectOrCreate?: ExplainabilityAnalysisCreateOrConnectWithoutSimulationInput | ExplainabilityAnalysisCreateOrConnectWithoutSimulationInput[]
    upsert?: ExplainabilityAnalysisUpsertWithWhereUniqueWithoutSimulationInput | ExplainabilityAnalysisUpsertWithWhereUniqueWithoutSimulationInput[]
    createMany?: ExplainabilityAnalysisCreateManySimulationInputEnvelope
    set?: ExplainabilityAnalysisWhereUniqueInput | ExplainabilityAnalysisWhereUniqueInput[]
    disconnect?: ExplainabilityAnalysisWhereUniqueInput | ExplainabilityAnalysisWhereUniqueInput[]
    delete?: ExplainabilityAnalysisWhereUniqueInput | ExplainabilityAnalysisWhereUniqueInput[]
    connect?: ExplainabilityAnalysisWhereUniqueInput | ExplainabilityAnalysisWhereUniqueInput[]
    update?: ExplainabilityAnalysisUpdateWithWhereUniqueWithoutSimulationInput | ExplainabilityAnalysisUpdateWithWhereUniqueWithoutSimulationInput[]
    updateMany?: ExplainabilityAnalysisUpdateManyWithWhereWithoutSimulationInput | ExplainabilityAnalysisUpdateManyWithWhereWithoutSimulationInput[]
    deleteMany?: ExplainabilityAnalysisScalarWhereInput | ExplainabilityAnalysisScalarWhereInput[]
  }

  export type ComplianceRecordUpdateManyWithoutSimulationNestedInput = {
    create?: XOR<ComplianceRecordCreateWithoutSimulationInput, ComplianceRecordUncheckedCreateWithoutSimulationInput> | ComplianceRecordCreateWithoutSimulationInput[] | ComplianceRecordUncheckedCreateWithoutSimulationInput[]
    connectOrCreate?: ComplianceRecordCreateOrConnectWithoutSimulationInput | ComplianceRecordCreateOrConnectWithoutSimulationInput[]
    upsert?: ComplianceRecordUpsertWithWhereUniqueWithoutSimulationInput | ComplianceRecordUpsertWithWhereUniqueWithoutSimulationInput[]
    createMany?: ComplianceRecordCreateManySimulationInputEnvelope
    set?: ComplianceRecordWhereUniqueInput | ComplianceRecordWhereUniqueInput[]
    disconnect?: ComplianceRecordWhereUniqueInput | ComplianceRecordWhereUniqueInput[]
    delete?: ComplianceRecordWhereUniqueInput | ComplianceRecordWhereUniqueInput[]
    connect?: ComplianceRecordWhereUniqueInput | ComplianceRecordWhereUniqueInput[]
    update?: ComplianceRecordUpdateWithWhereUniqueWithoutSimulationInput | ComplianceRecordUpdateWithWhereUniqueWithoutSimulationInput[]
    updateMany?: ComplianceRecordUpdateManyWithWhereWithoutSimulationInput | ComplianceRecordUpdateManyWithWhereWithoutSimulationInput[]
    deleteMany?: ComplianceRecordScalarWhereInput | ComplianceRecordScalarWhereInput[]
  }

  export type RiskAssessmentUpdateManyWithoutSimulationNestedInput = {
    create?: XOR<RiskAssessmentCreateWithoutSimulationInput, RiskAssessmentUncheckedCreateWithoutSimulationInput> | RiskAssessmentCreateWithoutSimulationInput[] | RiskAssessmentUncheckedCreateWithoutSimulationInput[]
    connectOrCreate?: RiskAssessmentCreateOrConnectWithoutSimulationInput | RiskAssessmentCreateOrConnectWithoutSimulationInput[]
    upsert?: RiskAssessmentUpsertWithWhereUniqueWithoutSimulationInput | RiskAssessmentUpsertWithWhereUniqueWithoutSimulationInput[]
    createMany?: RiskAssessmentCreateManySimulationInputEnvelope
    set?: RiskAssessmentWhereUniqueInput | RiskAssessmentWhereUniqueInput[]
    disconnect?: RiskAssessmentWhereUniqueInput | RiskAssessmentWhereUniqueInput[]
    delete?: RiskAssessmentWhereUniqueInput | RiskAssessmentWhereUniqueInput[]
    connect?: RiskAssessmentWhereUniqueInput | RiskAssessmentWhereUniqueInput[]
    update?: RiskAssessmentUpdateWithWhereUniqueWithoutSimulationInput | RiskAssessmentUpdateWithWhereUniqueWithoutSimulationInput[]
    updateMany?: RiskAssessmentUpdateManyWithWhereWithoutSimulationInput | RiskAssessmentUpdateManyWithWhereWithoutSimulationInput[]
    deleteMany?: RiskAssessmentScalarWhereInput | RiskAssessmentScalarWhereInput[]
  }

  export type AuditLogUpdateManyWithoutSimulationNestedInput = {
    create?: XOR<AuditLogCreateWithoutSimulationInput, AuditLogUncheckedCreateWithoutSimulationInput> | AuditLogCreateWithoutSimulationInput[] | AuditLogUncheckedCreateWithoutSimulationInput[]
    connectOrCreate?: AuditLogCreateOrConnectWithoutSimulationInput | AuditLogCreateOrConnectWithoutSimulationInput[]
    upsert?: AuditLogUpsertWithWhereUniqueWithoutSimulationInput | AuditLogUpsertWithWhereUniqueWithoutSimulationInput[]
    createMany?: AuditLogCreateManySimulationInputEnvelope
    set?: AuditLogWhereUniqueInput | AuditLogWhereUniqueInput[]
    disconnect?: AuditLogWhereUniqueInput | AuditLogWhereUniqueInput[]
    delete?: AuditLogWhereUniqueInput | AuditLogWhereUniqueInput[]
    connect?: AuditLogWhereUniqueInput | AuditLogWhereUniqueInput[]
    update?: AuditLogUpdateWithWhereUniqueWithoutSimulationInput | AuditLogUpdateWithWhereUniqueWithoutSimulationInput[]
    updateMany?: AuditLogUpdateManyWithWhereWithoutSimulationInput | AuditLogUpdateManyWithWhereWithoutSimulationInput[]
    deleteMany?: AuditLogScalarWhereInput | AuditLogScalarWhereInput[]
  }

  export type BiasDetectionResultUncheckedUpdateManyWithoutSimulationNestedInput = {
    create?: XOR<BiasDetectionResultCreateWithoutSimulationInput, BiasDetectionResultUncheckedCreateWithoutSimulationInput> | BiasDetectionResultCreateWithoutSimulationInput[] | BiasDetectionResultUncheckedCreateWithoutSimulationInput[]
    connectOrCreate?: BiasDetectionResultCreateOrConnectWithoutSimulationInput | BiasDetectionResultCreateOrConnectWithoutSimulationInput[]
    upsert?: BiasDetectionResultUpsertWithWhereUniqueWithoutSimulationInput | BiasDetectionResultUpsertWithWhereUniqueWithoutSimulationInput[]
    createMany?: BiasDetectionResultCreateManySimulationInputEnvelope
    set?: BiasDetectionResultWhereUniqueInput | BiasDetectionResultWhereUniqueInput[]
    disconnect?: BiasDetectionResultWhereUniqueInput | BiasDetectionResultWhereUniqueInput[]
    delete?: BiasDetectionResultWhereUniqueInput | BiasDetectionResultWhereUniqueInput[]
    connect?: BiasDetectionResultWhereUniqueInput | BiasDetectionResultWhereUniqueInput[]
    update?: BiasDetectionResultUpdateWithWhereUniqueWithoutSimulationInput | BiasDetectionResultUpdateWithWhereUniqueWithoutSimulationInput[]
    updateMany?: BiasDetectionResultUpdateManyWithWhereWithoutSimulationInput | BiasDetectionResultUpdateManyWithWhereWithoutSimulationInput[]
    deleteMany?: BiasDetectionResultScalarWhereInput | BiasDetectionResultScalarWhereInput[]
  }

  export type FairnessAssessmentUncheckedUpdateManyWithoutSimulationNestedInput = {
    create?: XOR<FairnessAssessmentCreateWithoutSimulationInput, FairnessAssessmentUncheckedCreateWithoutSimulationInput> | FairnessAssessmentCreateWithoutSimulationInput[] | FairnessAssessmentUncheckedCreateWithoutSimulationInput[]
    connectOrCreate?: FairnessAssessmentCreateOrConnectWithoutSimulationInput | FairnessAssessmentCreateOrConnectWithoutSimulationInput[]
    upsert?: FairnessAssessmentUpsertWithWhereUniqueWithoutSimulationInput | FairnessAssessmentUpsertWithWhereUniqueWithoutSimulationInput[]
    createMany?: FairnessAssessmentCreateManySimulationInputEnvelope
    set?: FairnessAssessmentWhereUniqueInput | FairnessAssessmentWhereUniqueInput[]
    disconnect?: FairnessAssessmentWhereUniqueInput | FairnessAssessmentWhereUniqueInput[]
    delete?: FairnessAssessmentWhereUniqueInput | FairnessAssessmentWhereUniqueInput[]
    connect?: FairnessAssessmentWhereUniqueInput | FairnessAssessmentWhereUniqueInput[]
    update?: FairnessAssessmentUpdateWithWhereUniqueWithoutSimulationInput | FairnessAssessmentUpdateWithWhereUniqueWithoutSimulationInput[]
    updateMany?: FairnessAssessmentUpdateManyWithWhereWithoutSimulationInput | FairnessAssessmentUpdateManyWithWhereWithoutSimulationInput[]
    deleteMany?: FairnessAssessmentScalarWhereInput | FairnessAssessmentScalarWhereInput[]
  }

  export type ExplainabilityAnalysisUncheckedUpdateManyWithoutSimulationNestedInput = {
    create?: XOR<ExplainabilityAnalysisCreateWithoutSimulationInput, ExplainabilityAnalysisUncheckedCreateWithoutSimulationInput> | ExplainabilityAnalysisCreateWithoutSimulationInput[] | ExplainabilityAnalysisUncheckedCreateWithoutSimulationInput[]
    connectOrCreate?: ExplainabilityAnalysisCreateOrConnectWithoutSimulationInput | ExplainabilityAnalysisCreateOrConnectWithoutSimulationInput[]
    upsert?: ExplainabilityAnalysisUpsertWithWhereUniqueWithoutSimulationInput | ExplainabilityAnalysisUpsertWithWhereUniqueWithoutSimulationInput[]
    createMany?: ExplainabilityAnalysisCreateManySimulationInputEnvelope
    set?: ExplainabilityAnalysisWhereUniqueInput | ExplainabilityAnalysisWhereUniqueInput[]
    disconnect?: ExplainabilityAnalysisWhereUniqueInput | ExplainabilityAnalysisWhereUniqueInput[]
    delete?: ExplainabilityAnalysisWhereUniqueInput | ExplainabilityAnalysisWhereUniqueInput[]
    connect?: ExplainabilityAnalysisWhereUniqueInput | ExplainabilityAnalysisWhereUniqueInput[]
    update?: ExplainabilityAnalysisUpdateWithWhereUniqueWithoutSimulationInput | ExplainabilityAnalysisUpdateWithWhereUniqueWithoutSimulationInput[]
    updateMany?: ExplainabilityAnalysisUpdateManyWithWhereWithoutSimulationInput | ExplainabilityAnalysisUpdateManyWithWhereWithoutSimulationInput[]
    deleteMany?: ExplainabilityAnalysisScalarWhereInput | ExplainabilityAnalysisScalarWhereInput[]
  }

  export type ComplianceRecordUncheckedUpdateManyWithoutSimulationNestedInput = {
    create?: XOR<ComplianceRecordCreateWithoutSimulationInput, ComplianceRecordUncheckedCreateWithoutSimulationInput> | ComplianceRecordCreateWithoutSimulationInput[] | ComplianceRecordUncheckedCreateWithoutSimulationInput[]
    connectOrCreate?: ComplianceRecordCreateOrConnectWithoutSimulationInput | ComplianceRecordCreateOrConnectWithoutSimulationInput[]
    upsert?: ComplianceRecordUpsertWithWhereUniqueWithoutSimulationInput | ComplianceRecordUpsertWithWhereUniqueWithoutSimulationInput[]
    createMany?: ComplianceRecordCreateManySimulationInputEnvelope
    set?: ComplianceRecordWhereUniqueInput | ComplianceRecordWhereUniqueInput[]
    disconnect?: ComplianceRecordWhereUniqueInput | ComplianceRecordWhereUniqueInput[]
    delete?: ComplianceRecordWhereUniqueInput | ComplianceRecordWhereUniqueInput[]
    connect?: ComplianceRecordWhereUniqueInput | ComplianceRecordWhereUniqueInput[]
    update?: ComplianceRecordUpdateWithWhereUniqueWithoutSimulationInput | ComplianceRecordUpdateWithWhereUniqueWithoutSimulationInput[]
    updateMany?: ComplianceRecordUpdateManyWithWhereWithoutSimulationInput | ComplianceRecordUpdateManyWithWhereWithoutSimulationInput[]
    deleteMany?: ComplianceRecordScalarWhereInput | ComplianceRecordScalarWhereInput[]
  }

  export type RiskAssessmentUncheckedUpdateManyWithoutSimulationNestedInput = {
    create?: XOR<RiskAssessmentCreateWithoutSimulationInput, RiskAssessmentUncheckedCreateWithoutSimulationInput> | RiskAssessmentCreateWithoutSimulationInput[] | RiskAssessmentUncheckedCreateWithoutSimulationInput[]
    connectOrCreate?: RiskAssessmentCreateOrConnectWithoutSimulationInput | RiskAssessmentCreateOrConnectWithoutSimulationInput[]
    upsert?: RiskAssessmentUpsertWithWhereUniqueWithoutSimulationInput | RiskAssessmentUpsertWithWhereUniqueWithoutSimulationInput[]
    createMany?: RiskAssessmentCreateManySimulationInputEnvelope
    set?: RiskAssessmentWhereUniqueInput | RiskAssessmentWhereUniqueInput[]
    disconnect?: RiskAssessmentWhereUniqueInput | RiskAssessmentWhereUniqueInput[]
    delete?: RiskAssessmentWhereUniqueInput | RiskAssessmentWhereUniqueInput[]
    connect?: RiskAssessmentWhereUniqueInput | RiskAssessmentWhereUniqueInput[]
    update?: RiskAssessmentUpdateWithWhereUniqueWithoutSimulationInput | RiskAssessmentUpdateWithWhereUniqueWithoutSimulationInput[]
    updateMany?: RiskAssessmentUpdateManyWithWhereWithoutSimulationInput | RiskAssessmentUpdateManyWithWhereWithoutSimulationInput[]
    deleteMany?: RiskAssessmentScalarWhereInput | RiskAssessmentScalarWhereInput[]
  }

  export type AuditLogUncheckedUpdateManyWithoutSimulationNestedInput = {
    create?: XOR<AuditLogCreateWithoutSimulationInput, AuditLogUncheckedCreateWithoutSimulationInput> | AuditLogCreateWithoutSimulationInput[] | AuditLogUncheckedCreateWithoutSimulationInput[]
    connectOrCreate?: AuditLogCreateOrConnectWithoutSimulationInput | AuditLogCreateOrConnectWithoutSimulationInput[]
    upsert?: AuditLogUpsertWithWhereUniqueWithoutSimulationInput | AuditLogUpsertWithWhereUniqueWithoutSimulationInput[]
    createMany?: AuditLogCreateManySimulationInputEnvelope
    set?: AuditLogWhereUniqueInput | AuditLogWhereUniqueInput[]
    disconnect?: AuditLogWhereUniqueInput | AuditLogWhereUniqueInput[]
    delete?: AuditLogWhereUniqueInput | AuditLogWhereUniqueInput[]
    connect?: AuditLogWhereUniqueInput | AuditLogWhereUniqueInput[]
    update?: AuditLogUpdateWithWhereUniqueWithoutSimulationInput | AuditLogUpdateWithWhereUniqueWithoutSimulationInput[]
    updateMany?: AuditLogUpdateManyWithWhereWithoutSimulationInput | AuditLogUpdateManyWithWhereWithoutSimulationInput[]
    deleteMany?: AuditLogScalarWhereInput | AuditLogScalarWhereInput[]
  }

  export type SimulationCreateNestedOneWithoutBiasDetectionResultInput = {
    create?: XOR<SimulationCreateWithoutBiasDetectionResultInput, SimulationUncheckedCreateWithoutBiasDetectionResultInput>
    connectOrCreate?: SimulationCreateOrConnectWithoutBiasDetectionResultInput
    connect?: SimulationWhereUniqueInput
  }

  export type SimulationUpdateOneRequiredWithoutBiasDetectionResultNestedInput = {
    create?: XOR<SimulationCreateWithoutBiasDetectionResultInput, SimulationUncheckedCreateWithoutBiasDetectionResultInput>
    connectOrCreate?: SimulationCreateOrConnectWithoutBiasDetectionResultInput
    upsert?: SimulationUpsertWithoutBiasDetectionResultInput
    connect?: SimulationWhereUniqueInput
    update?: XOR<XOR<SimulationUpdateToOneWithWhereWithoutBiasDetectionResultInput, SimulationUpdateWithoutBiasDetectionResultInput>, SimulationUncheckedUpdateWithoutBiasDetectionResultInput>
  }

  export type SimulationCreateNestedOneWithoutFairnessAssessmentInput = {
    create?: XOR<SimulationCreateWithoutFairnessAssessmentInput, SimulationUncheckedCreateWithoutFairnessAssessmentInput>
    connectOrCreate?: SimulationCreateOrConnectWithoutFairnessAssessmentInput
    connect?: SimulationWhereUniqueInput
  }

  export type SimulationUpdateOneRequiredWithoutFairnessAssessmentNestedInput = {
    create?: XOR<SimulationCreateWithoutFairnessAssessmentInput, SimulationUncheckedCreateWithoutFairnessAssessmentInput>
    connectOrCreate?: SimulationCreateOrConnectWithoutFairnessAssessmentInput
    upsert?: SimulationUpsertWithoutFairnessAssessmentInput
    connect?: SimulationWhereUniqueInput
    update?: XOR<XOR<SimulationUpdateToOneWithWhereWithoutFairnessAssessmentInput, SimulationUpdateWithoutFairnessAssessmentInput>, SimulationUncheckedUpdateWithoutFairnessAssessmentInput>
  }

  export type SimulationCreateNestedOneWithoutExplainabilityAnalysisInput = {
    create?: XOR<SimulationCreateWithoutExplainabilityAnalysisInput, SimulationUncheckedCreateWithoutExplainabilityAnalysisInput>
    connectOrCreate?: SimulationCreateOrConnectWithoutExplainabilityAnalysisInput
    connect?: SimulationWhereUniqueInput
  }

  export type SimulationUpdateOneRequiredWithoutExplainabilityAnalysisNestedInput = {
    create?: XOR<SimulationCreateWithoutExplainabilityAnalysisInput, SimulationUncheckedCreateWithoutExplainabilityAnalysisInput>
    connectOrCreate?: SimulationCreateOrConnectWithoutExplainabilityAnalysisInput
    upsert?: SimulationUpsertWithoutExplainabilityAnalysisInput
    connect?: SimulationWhereUniqueInput
    update?: XOR<XOR<SimulationUpdateToOneWithWhereWithoutExplainabilityAnalysisInput, SimulationUpdateWithoutExplainabilityAnalysisInput>, SimulationUncheckedUpdateWithoutExplainabilityAnalysisInput>
  }

  export type SimulationCreateNestedOneWithoutComplianceRecordInput = {
    create?: XOR<SimulationCreateWithoutComplianceRecordInput, SimulationUncheckedCreateWithoutComplianceRecordInput>
    connectOrCreate?: SimulationCreateOrConnectWithoutComplianceRecordInput
    connect?: SimulationWhereUniqueInput
  }

  export type SimulationUpdateOneRequiredWithoutComplianceRecordNestedInput = {
    create?: XOR<SimulationCreateWithoutComplianceRecordInput, SimulationUncheckedCreateWithoutComplianceRecordInput>
    connectOrCreate?: SimulationCreateOrConnectWithoutComplianceRecordInput
    upsert?: SimulationUpsertWithoutComplianceRecordInput
    connect?: SimulationWhereUniqueInput
    update?: XOR<XOR<SimulationUpdateToOneWithWhereWithoutComplianceRecordInput, SimulationUpdateWithoutComplianceRecordInput>, SimulationUncheckedUpdateWithoutComplianceRecordInput>
  }

  export type SimulationCreateNestedOneWithoutRiskAssessmentInput = {
    create?: XOR<SimulationCreateWithoutRiskAssessmentInput, SimulationUncheckedCreateWithoutRiskAssessmentInput>
    connectOrCreate?: SimulationCreateOrConnectWithoutRiskAssessmentInput
    connect?: SimulationWhereUniqueInput
  }

  export type SimulationUpdateOneRequiredWithoutRiskAssessmentNestedInput = {
    create?: XOR<SimulationCreateWithoutRiskAssessmentInput, SimulationUncheckedCreateWithoutRiskAssessmentInput>
    connectOrCreate?: SimulationCreateOrConnectWithoutRiskAssessmentInput
    upsert?: SimulationUpsertWithoutRiskAssessmentInput
    connect?: SimulationWhereUniqueInput
    update?: XOR<XOR<SimulationUpdateToOneWithWhereWithoutRiskAssessmentInput, SimulationUpdateWithoutRiskAssessmentInput>, SimulationUncheckedUpdateWithoutRiskAssessmentInput>
  }

  export type UserCreateNestedOneWithoutAuditLogsInput = {
    create?: XOR<UserCreateWithoutAuditLogsInput, UserUncheckedCreateWithoutAuditLogsInput>
    connectOrCreate?: UserCreateOrConnectWithoutAuditLogsInput
    connect?: UserWhereUniqueInput
  }

  export type SimulationCreateNestedOneWithoutAuditLogsInput = {
    create?: XOR<SimulationCreateWithoutAuditLogsInput, SimulationUncheckedCreateWithoutAuditLogsInput>
    connectOrCreate?: SimulationCreateOrConnectWithoutAuditLogsInput
    connect?: SimulationWhereUniqueInput
  }

  export type UserUpdateOneRequiredWithoutAuditLogsNestedInput = {
    create?: XOR<UserCreateWithoutAuditLogsInput, UserUncheckedCreateWithoutAuditLogsInput>
    connectOrCreate?: UserCreateOrConnectWithoutAuditLogsInput
    upsert?: UserUpsertWithoutAuditLogsInput
    connect?: UserWhereUniqueInput
    update?: XOR<XOR<UserUpdateToOneWithWhereWithoutAuditLogsInput, UserUpdateWithoutAuditLogsInput>, UserUncheckedUpdateWithoutAuditLogsInput>
  }

  export type SimulationUpdateOneWithoutAuditLogsNestedInput = {
    create?: XOR<SimulationCreateWithoutAuditLogsInput, SimulationUncheckedCreateWithoutAuditLogsInput>
    connectOrCreate?: SimulationCreateOrConnectWithoutAuditLogsInput
    upsert?: SimulationUpsertWithoutAuditLogsInput
    disconnect?: SimulationWhereInput | boolean
    delete?: SimulationWhereInput | boolean
    connect?: SimulationWhereUniqueInput
    update?: XOR<XOR<SimulationUpdateToOneWithWhereWithoutAuditLogsInput, SimulationUpdateWithoutAuditLogsInput>, SimulationUncheckedUpdateWithoutAuditLogsInput>
  }

  export type NullableIntFieldUpdateOperationsInput = {
    set?: number | null
    increment?: number
    decrement?: number
    multiply?: number
    divide?: number
  }

  export type NestedIntFilter<$PrismaModel = never> = {
    equals?: number | IntFieldRefInput<$PrismaModel>
    in?: number[] | ListIntFieldRefInput<$PrismaModel>
    notIn?: number[] | ListIntFieldRefInput<$PrismaModel>
    lt?: number | IntFieldRefInput<$PrismaModel>
    lte?: number | IntFieldRefInput<$PrismaModel>
    gt?: number | IntFieldRefInput<$PrismaModel>
    gte?: number | IntFieldRefInput<$PrismaModel>
    not?: NestedIntFilter<$PrismaModel> | number
  }

  export type NestedDateTimeFilter<$PrismaModel = never> = {
    equals?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    in?: Date[] | string[] | ListDateTimeFieldRefInput<$PrismaModel>
    notIn?: Date[] | string[] | ListDateTimeFieldRefInput<$PrismaModel>
    lt?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    lte?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    gt?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    gte?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    not?: NestedDateTimeFilter<$PrismaModel> | Date | string
  }

  export type NestedStringFilter<$PrismaModel = never> = {
    equals?: string | StringFieldRefInput<$PrismaModel>
    in?: string[] | ListStringFieldRefInput<$PrismaModel>
    notIn?: string[] | ListStringFieldRefInput<$PrismaModel>
    lt?: string | StringFieldRefInput<$PrismaModel>
    lte?: string | StringFieldRefInput<$PrismaModel>
    gt?: string | StringFieldRefInput<$PrismaModel>
    gte?: string | StringFieldRefInput<$PrismaModel>
    contains?: string | StringFieldRefInput<$PrismaModel>
    startsWith?: string | StringFieldRefInput<$PrismaModel>
    endsWith?: string | StringFieldRefInput<$PrismaModel>
    not?: NestedStringFilter<$PrismaModel> | string
  }

  export type NestedIntWithAggregatesFilter<$PrismaModel = never> = {
    equals?: number | IntFieldRefInput<$PrismaModel>
    in?: number[] | ListIntFieldRefInput<$PrismaModel>
    notIn?: number[] | ListIntFieldRefInput<$PrismaModel>
    lt?: number | IntFieldRefInput<$PrismaModel>
    lte?: number | IntFieldRefInput<$PrismaModel>
    gt?: number | IntFieldRefInput<$PrismaModel>
    gte?: number | IntFieldRefInput<$PrismaModel>
    not?: NestedIntWithAggregatesFilter<$PrismaModel> | number
    _count?: NestedIntFilter<$PrismaModel>
    _avg?: NestedFloatFilter<$PrismaModel>
    _sum?: NestedIntFilter<$PrismaModel>
    _min?: NestedIntFilter<$PrismaModel>
    _max?: NestedIntFilter<$PrismaModel>
  }

  export type NestedFloatFilter<$PrismaModel = never> = {
    equals?: number | FloatFieldRefInput<$PrismaModel>
    in?: number[] | ListFloatFieldRefInput<$PrismaModel>
    notIn?: number[] | ListFloatFieldRefInput<$PrismaModel>
    lt?: number | FloatFieldRefInput<$PrismaModel>
    lte?: number | FloatFieldRefInput<$PrismaModel>
    gt?: number | FloatFieldRefInput<$PrismaModel>
    gte?: number | FloatFieldRefInput<$PrismaModel>
    not?: NestedFloatFilter<$PrismaModel> | number
  }

  export type NestedDateTimeWithAggregatesFilter<$PrismaModel = never> = {
    equals?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    in?: Date[] | string[] | ListDateTimeFieldRefInput<$PrismaModel>
    notIn?: Date[] | string[] | ListDateTimeFieldRefInput<$PrismaModel>
    lt?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    lte?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    gt?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    gte?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    not?: NestedDateTimeWithAggregatesFilter<$PrismaModel> | Date | string
    _count?: NestedIntFilter<$PrismaModel>
    _min?: NestedDateTimeFilter<$PrismaModel>
    _max?: NestedDateTimeFilter<$PrismaModel>
  }

  export type NestedStringWithAggregatesFilter<$PrismaModel = never> = {
    equals?: string | StringFieldRefInput<$PrismaModel>
    in?: string[] | ListStringFieldRefInput<$PrismaModel>
    notIn?: string[] | ListStringFieldRefInput<$PrismaModel>
    lt?: string | StringFieldRefInput<$PrismaModel>
    lte?: string | StringFieldRefInput<$PrismaModel>
    gt?: string | StringFieldRefInput<$PrismaModel>
    gte?: string | StringFieldRefInput<$PrismaModel>
    contains?: string | StringFieldRefInput<$PrismaModel>
    startsWith?: string | StringFieldRefInput<$PrismaModel>
    endsWith?: string | StringFieldRefInput<$PrismaModel>
    not?: NestedStringWithAggregatesFilter<$PrismaModel> | string
    _count?: NestedIntFilter<$PrismaModel>
    _min?: NestedStringFilter<$PrismaModel>
    _max?: NestedStringFilter<$PrismaModel>
  }

  export type NestedStringNullableFilter<$PrismaModel = never> = {
    equals?: string | StringFieldRefInput<$PrismaModel> | null
    in?: string[] | ListStringFieldRefInput<$PrismaModel> | null
    notIn?: string[] | ListStringFieldRefInput<$PrismaModel> | null
    lt?: string | StringFieldRefInput<$PrismaModel>
    lte?: string | StringFieldRefInput<$PrismaModel>
    gt?: string | StringFieldRefInput<$PrismaModel>
    gte?: string | StringFieldRefInput<$PrismaModel>
    contains?: string | StringFieldRefInput<$PrismaModel>
    startsWith?: string | StringFieldRefInput<$PrismaModel>
    endsWith?: string | StringFieldRefInput<$PrismaModel>
    not?: NestedStringNullableFilter<$PrismaModel> | string | null
  }

  export type NestedEnumSimulationStatusFilter<$PrismaModel = never> = {
    equals?: $Enums.SimulationStatus | EnumSimulationStatusFieldRefInput<$PrismaModel>
    in?: $Enums.SimulationStatus[] | ListEnumSimulationStatusFieldRefInput<$PrismaModel>
    notIn?: $Enums.SimulationStatus[] | ListEnumSimulationStatusFieldRefInput<$PrismaModel>
    not?: NestedEnumSimulationStatusFilter<$PrismaModel> | $Enums.SimulationStatus
  }

  export type NestedStringNullableWithAggregatesFilter<$PrismaModel = never> = {
    equals?: string | StringFieldRefInput<$PrismaModel> | null
    in?: string[] | ListStringFieldRefInput<$PrismaModel> | null
    notIn?: string[] | ListStringFieldRefInput<$PrismaModel> | null
    lt?: string | StringFieldRefInput<$PrismaModel>
    lte?: string | StringFieldRefInput<$PrismaModel>
    gt?: string | StringFieldRefInput<$PrismaModel>
    gte?: string | StringFieldRefInput<$PrismaModel>
    contains?: string | StringFieldRefInput<$PrismaModel>
    startsWith?: string | StringFieldRefInput<$PrismaModel>
    endsWith?: string | StringFieldRefInput<$PrismaModel>
    not?: NestedStringNullableWithAggregatesFilter<$PrismaModel> | string | null
    _count?: NestedIntNullableFilter<$PrismaModel>
    _min?: NestedStringNullableFilter<$PrismaModel>
    _max?: NestedStringNullableFilter<$PrismaModel>
  }

  export type NestedIntNullableFilter<$PrismaModel = never> = {
    equals?: number | IntFieldRefInput<$PrismaModel> | null
    in?: number[] | ListIntFieldRefInput<$PrismaModel> | null
    notIn?: number[] | ListIntFieldRefInput<$PrismaModel> | null
    lt?: number | IntFieldRefInput<$PrismaModel>
    lte?: number | IntFieldRefInput<$PrismaModel>
    gt?: number | IntFieldRefInput<$PrismaModel>
    gte?: number | IntFieldRefInput<$PrismaModel>
    not?: NestedIntNullableFilter<$PrismaModel> | number | null
  }

  export type NestedEnumSimulationStatusWithAggregatesFilter<$PrismaModel = never> = {
    equals?: $Enums.SimulationStatus | EnumSimulationStatusFieldRefInput<$PrismaModel>
    in?: $Enums.SimulationStatus[] | ListEnumSimulationStatusFieldRefInput<$PrismaModel>
    notIn?: $Enums.SimulationStatus[] | ListEnumSimulationStatusFieldRefInput<$PrismaModel>
    not?: NestedEnumSimulationStatusWithAggregatesFilter<$PrismaModel> | $Enums.SimulationStatus
    _count?: NestedIntFilter<$PrismaModel>
    _min?: NestedEnumSimulationStatusFilter<$PrismaModel>
    _max?: NestedEnumSimulationStatusFilter<$PrismaModel>
  }
  export type NestedJsonFilter<$PrismaModel = never> =
    | PatchUndefined<
        Either<Required<NestedJsonFilterBase<$PrismaModel>>, Exclude<keyof Required<NestedJsonFilterBase<$PrismaModel>>, 'path'>>,
        Required<NestedJsonFilterBase<$PrismaModel>>
      >
    | OptionalFlat<Omit<Required<NestedJsonFilterBase<$PrismaModel>>, 'path'>>

  export type NestedJsonFilterBase<$PrismaModel = never> = {
    equals?: InputJsonValue | JsonFieldRefInput<$PrismaModel> | JsonNullValueFilter
    path?: string[]
    mode?: QueryMode | EnumQueryModeFieldRefInput<$PrismaModel>
    string_contains?: string | StringFieldRefInput<$PrismaModel>
    string_starts_with?: string | StringFieldRefInput<$PrismaModel>
    string_ends_with?: string | StringFieldRefInput<$PrismaModel>
    array_starts_with?: InputJsonValue | JsonFieldRefInput<$PrismaModel> | null
    array_ends_with?: InputJsonValue | JsonFieldRefInput<$PrismaModel> | null
    array_contains?: InputJsonValue | JsonFieldRefInput<$PrismaModel> | null
    lt?: InputJsonValue | JsonFieldRefInput<$PrismaModel>
    lte?: InputJsonValue | JsonFieldRefInput<$PrismaModel>
    gt?: InputJsonValue | JsonFieldRefInput<$PrismaModel>
    gte?: InputJsonValue | JsonFieldRefInput<$PrismaModel>
    not?: InputJsonValue | JsonFieldRefInput<$PrismaModel> | JsonNullValueFilter
  }

  export type NestedIntNullableWithAggregatesFilter<$PrismaModel = never> = {
    equals?: number | IntFieldRefInput<$PrismaModel> | null
    in?: number[] | ListIntFieldRefInput<$PrismaModel> | null
    notIn?: number[] | ListIntFieldRefInput<$PrismaModel> | null
    lt?: number | IntFieldRefInput<$PrismaModel>
    lte?: number | IntFieldRefInput<$PrismaModel>
    gt?: number | IntFieldRefInput<$PrismaModel>
    gte?: number | IntFieldRefInput<$PrismaModel>
    not?: NestedIntNullableWithAggregatesFilter<$PrismaModel> | number | null
    _count?: NestedIntNullableFilter<$PrismaModel>
    _avg?: NestedFloatNullableFilter<$PrismaModel>
    _sum?: NestedIntNullableFilter<$PrismaModel>
    _min?: NestedIntNullableFilter<$PrismaModel>
    _max?: NestedIntNullableFilter<$PrismaModel>
  }

  export type NestedFloatNullableFilter<$PrismaModel = never> = {
    equals?: number | FloatFieldRefInput<$PrismaModel> | null
    in?: number[] | ListFloatFieldRefInput<$PrismaModel> | null
    notIn?: number[] | ListFloatFieldRefInput<$PrismaModel> | null
    lt?: number | FloatFieldRefInput<$PrismaModel>
    lte?: number | FloatFieldRefInput<$PrismaModel>
    gt?: number | FloatFieldRefInput<$PrismaModel>
    gte?: number | FloatFieldRefInput<$PrismaModel>
    not?: NestedFloatNullableFilter<$PrismaModel> | number | null
  }

  export type SimulationCreateWithoutUserInput = {
    createdAt?: Date | string
    updatedAt?: Date | string
    name: string
    description?: string | null
    status: $Enums.SimulationStatus
    config: JsonNullValueInput | InputJsonValue
    modelType: string
    version: string
    tags?: SimulationCreatetagsInput | string[]
    BiasDetectionResult?: BiasDetectionResultCreateNestedManyWithoutSimulationInput
    FairnessAssessment?: FairnessAssessmentCreateNestedManyWithoutSimulationInput
    ExplainabilityAnalysis?: ExplainabilityAnalysisCreateNestedManyWithoutSimulationInput
    ComplianceRecord?: ComplianceRecordCreateNestedManyWithoutSimulationInput
    RiskAssessment?: RiskAssessmentCreateNestedManyWithoutSimulationInput
    auditLogs?: AuditLogCreateNestedManyWithoutSimulationInput
  }

  export type SimulationUncheckedCreateWithoutUserInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    name: string
    description?: string | null
    status: $Enums.SimulationStatus
    config: JsonNullValueInput | InputJsonValue
    modelType: string
    version: string
    tags?: SimulationCreatetagsInput | string[]
    BiasDetectionResult?: BiasDetectionResultUncheckedCreateNestedManyWithoutSimulationInput
    FairnessAssessment?: FairnessAssessmentUncheckedCreateNestedManyWithoutSimulationInput
    ExplainabilityAnalysis?: ExplainabilityAnalysisUncheckedCreateNestedManyWithoutSimulationInput
    ComplianceRecord?: ComplianceRecordUncheckedCreateNestedManyWithoutSimulationInput
    RiskAssessment?: RiskAssessmentUncheckedCreateNestedManyWithoutSimulationInput
    auditLogs?: AuditLogUncheckedCreateNestedManyWithoutSimulationInput
  }

  export type SimulationCreateOrConnectWithoutUserInput = {
    where: SimulationWhereUniqueInput
    create: XOR<SimulationCreateWithoutUserInput, SimulationUncheckedCreateWithoutUserInput>
  }

  export type SimulationCreateManyUserInputEnvelope = {
    data: SimulationCreateManyUserInput | SimulationCreateManyUserInput[]
    skipDuplicates?: boolean
  }

  export type AuditLogCreateWithoutUserInput = {
    createdAt?: Date | string
    action: string
    details: JsonNullValueInput | InputJsonValue
    ipAddress: string
    userAgent: string
    simulation?: SimulationCreateNestedOneWithoutAuditLogsInput
  }

  export type AuditLogUncheckedCreateWithoutUserInput = {
    id?: number
    createdAt?: Date | string
    simulationId?: number | null
    action: string
    details: JsonNullValueInput | InputJsonValue
    ipAddress: string
    userAgent: string
  }

  export type AuditLogCreateOrConnectWithoutUserInput = {
    where: AuditLogWhereUniqueInput
    create: XOR<AuditLogCreateWithoutUserInput, AuditLogUncheckedCreateWithoutUserInput>
  }

  export type AuditLogCreateManyUserInputEnvelope = {
    data: AuditLogCreateManyUserInput | AuditLogCreateManyUserInput[]
    skipDuplicates?: boolean
  }

  export type SimulationUpsertWithWhereUniqueWithoutUserInput = {
    where: SimulationWhereUniqueInput
    update: XOR<SimulationUpdateWithoutUserInput, SimulationUncheckedUpdateWithoutUserInput>
    create: XOR<SimulationCreateWithoutUserInput, SimulationUncheckedCreateWithoutUserInput>
  }

  export type SimulationUpdateWithWhereUniqueWithoutUserInput = {
    where: SimulationWhereUniqueInput
    data: XOR<SimulationUpdateWithoutUserInput, SimulationUncheckedUpdateWithoutUserInput>
  }

  export type SimulationUpdateManyWithWhereWithoutUserInput = {
    where: SimulationScalarWhereInput
    data: XOR<SimulationUpdateManyMutationInput, SimulationUncheckedUpdateManyWithoutUserInput>
  }

  export type SimulationScalarWhereInput = {
    AND?: SimulationScalarWhereInput | SimulationScalarWhereInput[]
    OR?: SimulationScalarWhereInput[]
    NOT?: SimulationScalarWhereInput | SimulationScalarWhereInput[]
    id?: IntFilter<"Simulation"> | number
    createdAt?: DateTimeFilter<"Simulation"> | Date | string
    updatedAt?: DateTimeFilter<"Simulation"> | Date | string
    name?: StringFilter<"Simulation"> | string
    description?: StringNullableFilter<"Simulation"> | string | null
    status?: EnumSimulationStatusFilter<"Simulation"> | $Enums.SimulationStatus
    userId?: IntFilter<"Simulation"> | number
    config?: JsonFilter<"Simulation">
    modelType?: StringFilter<"Simulation"> | string
    version?: StringFilter<"Simulation"> | string
    tags?: StringNullableListFilter<"Simulation">
  }

  export type AuditLogUpsertWithWhereUniqueWithoutUserInput = {
    where: AuditLogWhereUniqueInput
    update: XOR<AuditLogUpdateWithoutUserInput, AuditLogUncheckedUpdateWithoutUserInput>
    create: XOR<AuditLogCreateWithoutUserInput, AuditLogUncheckedCreateWithoutUserInput>
  }

  export type AuditLogUpdateWithWhereUniqueWithoutUserInput = {
    where: AuditLogWhereUniqueInput
    data: XOR<AuditLogUpdateWithoutUserInput, AuditLogUncheckedUpdateWithoutUserInput>
  }

  export type AuditLogUpdateManyWithWhereWithoutUserInput = {
    where: AuditLogScalarWhereInput
    data: XOR<AuditLogUpdateManyMutationInput, AuditLogUncheckedUpdateManyWithoutUserInput>
  }

  export type AuditLogScalarWhereInput = {
    AND?: AuditLogScalarWhereInput | AuditLogScalarWhereInput[]
    OR?: AuditLogScalarWhereInput[]
    NOT?: AuditLogScalarWhereInput | AuditLogScalarWhereInput[]
    id?: IntFilter<"AuditLog"> | number
    createdAt?: DateTimeFilter<"AuditLog"> | Date | string
    userId?: IntFilter<"AuditLog"> | number
    simulationId?: IntNullableFilter<"AuditLog"> | number | null
    action?: StringFilter<"AuditLog"> | string
    details?: JsonFilter<"AuditLog">
    ipAddress?: StringFilter<"AuditLog"> | string
    userAgent?: StringFilter<"AuditLog"> | string
  }

  export type UserCreateWithoutSimulationsInput = {
    createdAt?: Date | string
    updatedAt?: Date | string
    email: string
    passwordHash: string
    name: string
    role?: string
    auditLogs?: AuditLogCreateNestedManyWithoutUserInput
  }

  export type UserUncheckedCreateWithoutSimulationsInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    email: string
    passwordHash: string
    name: string
    role?: string
    auditLogs?: AuditLogUncheckedCreateNestedManyWithoutUserInput
  }

  export type UserCreateOrConnectWithoutSimulationsInput = {
    where: UserWhereUniqueInput
    create: XOR<UserCreateWithoutSimulationsInput, UserUncheckedCreateWithoutSimulationsInput>
  }

  export type BiasDetectionResultCreateWithoutSimulationInput = {
    createdAt?: Date | string
    updatedAt?: Date | string
    result: JsonNullValueInput | InputJsonValue
  }

  export type BiasDetectionResultUncheckedCreateWithoutSimulationInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    result: JsonNullValueInput | InputJsonValue
  }

  export type BiasDetectionResultCreateOrConnectWithoutSimulationInput = {
    where: BiasDetectionResultWhereUniqueInput
    create: XOR<BiasDetectionResultCreateWithoutSimulationInput, BiasDetectionResultUncheckedCreateWithoutSimulationInput>
  }

  export type BiasDetectionResultCreateManySimulationInputEnvelope = {
    data: BiasDetectionResultCreateManySimulationInput | BiasDetectionResultCreateManySimulationInput[]
    skipDuplicates?: boolean
  }

  export type FairnessAssessmentCreateWithoutSimulationInput = {
    createdAt?: Date | string
    updatedAt?: Date | string
    assessment: JsonNullValueInput | InputJsonValue
  }

  export type FairnessAssessmentUncheckedCreateWithoutSimulationInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    assessment: JsonNullValueInput | InputJsonValue
  }

  export type FairnessAssessmentCreateOrConnectWithoutSimulationInput = {
    where: FairnessAssessmentWhereUniqueInput
    create: XOR<FairnessAssessmentCreateWithoutSimulationInput, FairnessAssessmentUncheckedCreateWithoutSimulationInput>
  }

  export type FairnessAssessmentCreateManySimulationInputEnvelope = {
    data: FairnessAssessmentCreateManySimulationInput | FairnessAssessmentCreateManySimulationInput[]
    skipDuplicates?: boolean
  }

  export type ExplainabilityAnalysisCreateWithoutSimulationInput = {
    createdAt?: Date | string
    updatedAt?: Date | string
    analysis: JsonNullValueInput | InputJsonValue
  }

  export type ExplainabilityAnalysisUncheckedCreateWithoutSimulationInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    analysis: JsonNullValueInput | InputJsonValue
  }

  export type ExplainabilityAnalysisCreateOrConnectWithoutSimulationInput = {
    where: ExplainabilityAnalysisWhereUniqueInput
    create: XOR<ExplainabilityAnalysisCreateWithoutSimulationInput, ExplainabilityAnalysisUncheckedCreateWithoutSimulationInput>
  }

  export type ExplainabilityAnalysisCreateManySimulationInputEnvelope = {
    data: ExplainabilityAnalysisCreateManySimulationInput | ExplainabilityAnalysisCreateManySimulationInput[]
    skipDuplicates?: boolean
  }

  export type ComplianceRecordCreateWithoutSimulationInput = {
    createdAt?: Date | string
    updatedAt?: Date | string
    record: JsonNullValueInput | InputJsonValue
  }

  export type ComplianceRecordUncheckedCreateWithoutSimulationInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    record: JsonNullValueInput | InputJsonValue
  }

  export type ComplianceRecordCreateOrConnectWithoutSimulationInput = {
    where: ComplianceRecordWhereUniqueInput
    create: XOR<ComplianceRecordCreateWithoutSimulationInput, ComplianceRecordUncheckedCreateWithoutSimulationInput>
  }

  export type ComplianceRecordCreateManySimulationInputEnvelope = {
    data: ComplianceRecordCreateManySimulationInput | ComplianceRecordCreateManySimulationInput[]
    skipDuplicates?: boolean
  }

  export type RiskAssessmentCreateWithoutSimulationInput = {
    createdAt?: Date | string
    updatedAt?: Date | string
    assessment: JsonNullValueInput | InputJsonValue
  }

  export type RiskAssessmentUncheckedCreateWithoutSimulationInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    assessment: JsonNullValueInput | InputJsonValue
  }

  export type RiskAssessmentCreateOrConnectWithoutSimulationInput = {
    where: RiskAssessmentWhereUniqueInput
    create: XOR<RiskAssessmentCreateWithoutSimulationInput, RiskAssessmentUncheckedCreateWithoutSimulationInput>
  }

  export type RiskAssessmentCreateManySimulationInputEnvelope = {
    data: RiskAssessmentCreateManySimulationInput | RiskAssessmentCreateManySimulationInput[]
    skipDuplicates?: boolean
  }

  export type AuditLogCreateWithoutSimulationInput = {
    createdAt?: Date | string
    action: string
    details: JsonNullValueInput | InputJsonValue
    ipAddress: string
    userAgent: string
    user: UserCreateNestedOneWithoutAuditLogsInput
  }

  export type AuditLogUncheckedCreateWithoutSimulationInput = {
    id?: number
    createdAt?: Date | string
    userId: number
    action: string
    details: JsonNullValueInput | InputJsonValue
    ipAddress: string
    userAgent: string
  }

  export type AuditLogCreateOrConnectWithoutSimulationInput = {
    where: AuditLogWhereUniqueInput
    create: XOR<AuditLogCreateWithoutSimulationInput, AuditLogUncheckedCreateWithoutSimulationInput>
  }

  export type AuditLogCreateManySimulationInputEnvelope = {
    data: AuditLogCreateManySimulationInput | AuditLogCreateManySimulationInput[]
    skipDuplicates?: boolean
  }

  export type UserUpsertWithoutSimulationsInput = {
    update: XOR<UserUpdateWithoutSimulationsInput, UserUncheckedUpdateWithoutSimulationsInput>
    create: XOR<UserCreateWithoutSimulationsInput, UserUncheckedCreateWithoutSimulationsInput>
    where?: UserWhereInput
  }

  export type UserUpdateToOneWithWhereWithoutSimulationsInput = {
    where?: UserWhereInput
    data: XOR<UserUpdateWithoutSimulationsInput, UserUncheckedUpdateWithoutSimulationsInput>
  }

  export type UserUpdateWithoutSimulationsInput = {
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    email?: StringFieldUpdateOperationsInput | string
    passwordHash?: StringFieldUpdateOperationsInput | string
    name?: StringFieldUpdateOperationsInput | string
    role?: StringFieldUpdateOperationsInput | string
    auditLogs?: AuditLogUpdateManyWithoutUserNestedInput
  }

  export type UserUncheckedUpdateWithoutSimulationsInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    email?: StringFieldUpdateOperationsInput | string
    passwordHash?: StringFieldUpdateOperationsInput | string
    name?: StringFieldUpdateOperationsInput | string
    role?: StringFieldUpdateOperationsInput | string
    auditLogs?: AuditLogUncheckedUpdateManyWithoutUserNestedInput
  }

  export type BiasDetectionResultUpsertWithWhereUniqueWithoutSimulationInput = {
    where: BiasDetectionResultWhereUniqueInput
    update: XOR<BiasDetectionResultUpdateWithoutSimulationInput, BiasDetectionResultUncheckedUpdateWithoutSimulationInput>
    create: XOR<BiasDetectionResultCreateWithoutSimulationInput, BiasDetectionResultUncheckedCreateWithoutSimulationInput>
  }

  export type BiasDetectionResultUpdateWithWhereUniqueWithoutSimulationInput = {
    where: BiasDetectionResultWhereUniqueInput
    data: XOR<BiasDetectionResultUpdateWithoutSimulationInput, BiasDetectionResultUncheckedUpdateWithoutSimulationInput>
  }

  export type BiasDetectionResultUpdateManyWithWhereWithoutSimulationInput = {
    where: BiasDetectionResultScalarWhereInput
    data: XOR<BiasDetectionResultUpdateManyMutationInput, BiasDetectionResultUncheckedUpdateManyWithoutSimulationInput>
  }

  export type BiasDetectionResultScalarWhereInput = {
    AND?: BiasDetectionResultScalarWhereInput | BiasDetectionResultScalarWhereInput[]
    OR?: BiasDetectionResultScalarWhereInput[]
    NOT?: BiasDetectionResultScalarWhereInput | BiasDetectionResultScalarWhereInput[]
    id?: IntFilter<"BiasDetectionResult"> | number
    createdAt?: DateTimeFilter<"BiasDetectionResult"> | Date | string
    updatedAt?: DateTimeFilter<"BiasDetectionResult"> | Date | string
    simulationId?: IntFilter<"BiasDetectionResult"> | number
    result?: JsonFilter<"BiasDetectionResult">
  }

  export type FairnessAssessmentUpsertWithWhereUniqueWithoutSimulationInput = {
    where: FairnessAssessmentWhereUniqueInput
    update: XOR<FairnessAssessmentUpdateWithoutSimulationInput, FairnessAssessmentUncheckedUpdateWithoutSimulationInput>
    create: XOR<FairnessAssessmentCreateWithoutSimulationInput, FairnessAssessmentUncheckedCreateWithoutSimulationInput>
  }

  export type FairnessAssessmentUpdateWithWhereUniqueWithoutSimulationInput = {
    where: FairnessAssessmentWhereUniqueInput
    data: XOR<FairnessAssessmentUpdateWithoutSimulationInput, FairnessAssessmentUncheckedUpdateWithoutSimulationInput>
  }

  export type FairnessAssessmentUpdateManyWithWhereWithoutSimulationInput = {
    where: FairnessAssessmentScalarWhereInput
    data: XOR<FairnessAssessmentUpdateManyMutationInput, FairnessAssessmentUncheckedUpdateManyWithoutSimulationInput>
  }

  export type FairnessAssessmentScalarWhereInput = {
    AND?: FairnessAssessmentScalarWhereInput | FairnessAssessmentScalarWhereInput[]
    OR?: FairnessAssessmentScalarWhereInput[]
    NOT?: FairnessAssessmentScalarWhereInput | FairnessAssessmentScalarWhereInput[]
    id?: IntFilter<"FairnessAssessment"> | number
    createdAt?: DateTimeFilter<"FairnessAssessment"> | Date | string
    updatedAt?: DateTimeFilter<"FairnessAssessment"> | Date | string
    simulationId?: IntFilter<"FairnessAssessment"> | number
    assessment?: JsonFilter<"FairnessAssessment">
  }

  export type ExplainabilityAnalysisUpsertWithWhereUniqueWithoutSimulationInput = {
    where: ExplainabilityAnalysisWhereUniqueInput
    update: XOR<ExplainabilityAnalysisUpdateWithoutSimulationInput, ExplainabilityAnalysisUncheckedUpdateWithoutSimulationInput>
    create: XOR<ExplainabilityAnalysisCreateWithoutSimulationInput, ExplainabilityAnalysisUncheckedCreateWithoutSimulationInput>
  }

  export type ExplainabilityAnalysisUpdateWithWhereUniqueWithoutSimulationInput = {
    where: ExplainabilityAnalysisWhereUniqueInput
    data: XOR<ExplainabilityAnalysisUpdateWithoutSimulationInput, ExplainabilityAnalysisUncheckedUpdateWithoutSimulationInput>
  }

  export type ExplainabilityAnalysisUpdateManyWithWhereWithoutSimulationInput = {
    where: ExplainabilityAnalysisScalarWhereInput
    data: XOR<ExplainabilityAnalysisUpdateManyMutationInput, ExplainabilityAnalysisUncheckedUpdateManyWithoutSimulationInput>
  }

  export type ExplainabilityAnalysisScalarWhereInput = {
    AND?: ExplainabilityAnalysisScalarWhereInput | ExplainabilityAnalysisScalarWhereInput[]
    OR?: ExplainabilityAnalysisScalarWhereInput[]
    NOT?: ExplainabilityAnalysisScalarWhereInput | ExplainabilityAnalysisScalarWhereInput[]
    id?: IntFilter<"ExplainabilityAnalysis"> | number
    createdAt?: DateTimeFilter<"ExplainabilityAnalysis"> | Date | string
    updatedAt?: DateTimeFilter<"ExplainabilityAnalysis"> | Date | string
    simulationId?: IntFilter<"ExplainabilityAnalysis"> | number
    analysis?: JsonFilter<"ExplainabilityAnalysis">
  }

  export type ComplianceRecordUpsertWithWhereUniqueWithoutSimulationInput = {
    where: ComplianceRecordWhereUniqueInput
    update: XOR<ComplianceRecordUpdateWithoutSimulationInput, ComplianceRecordUncheckedUpdateWithoutSimulationInput>
    create: XOR<ComplianceRecordCreateWithoutSimulationInput, ComplianceRecordUncheckedCreateWithoutSimulationInput>
  }

  export type ComplianceRecordUpdateWithWhereUniqueWithoutSimulationInput = {
    where: ComplianceRecordWhereUniqueInput
    data: XOR<ComplianceRecordUpdateWithoutSimulationInput, ComplianceRecordUncheckedUpdateWithoutSimulationInput>
  }

  export type ComplianceRecordUpdateManyWithWhereWithoutSimulationInput = {
    where: ComplianceRecordScalarWhereInput
    data: XOR<ComplianceRecordUpdateManyMutationInput, ComplianceRecordUncheckedUpdateManyWithoutSimulationInput>
  }

  export type ComplianceRecordScalarWhereInput = {
    AND?: ComplianceRecordScalarWhereInput | ComplianceRecordScalarWhereInput[]
    OR?: ComplianceRecordScalarWhereInput[]
    NOT?: ComplianceRecordScalarWhereInput | ComplianceRecordScalarWhereInput[]
    id?: IntFilter<"ComplianceRecord"> | number
    createdAt?: DateTimeFilter<"ComplianceRecord"> | Date | string
    updatedAt?: DateTimeFilter<"ComplianceRecord"> | Date | string
    simulationId?: IntFilter<"ComplianceRecord"> | number
    record?: JsonFilter<"ComplianceRecord">
  }

  export type RiskAssessmentUpsertWithWhereUniqueWithoutSimulationInput = {
    where: RiskAssessmentWhereUniqueInput
    update: XOR<RiskAssessmentUpdateWithoutSimulationInput, RiskAssessmentUncheckedUpdateWithoutSimulationInput>
    create: XOR<RiskAssessmentCreateWithoutSimulationInput, RiskAssessmentUncheckedCreateWithoutSimulationInput>
  }

  export type RiskAssessmentUpdateWithWhereUniqueWithoutSimulationInput = {
    where: RiskAssessmentWhereUniqueInput
    data: XOR<RiskAssessmentUpdateWithoutSimulationInput, RiskAssessmentUncheckedUpdateWithoutSimulationInput>
  }

  export type RiskAssessmentUpdateManyWithWhereWithoutSimulationInput = {
    where: RiskAssessmentScalarWhereInput
    data: XOR<RiskAssessmentUpdateManyMutationInput, RiskAssessmentUncheckedUpdateManyWithoutSimulationInput>
  }

  export type RiskAssessmentScalarWhereInput = {
    AND?: RiskAssessmentScalarWhereInput | RiskAssessmentScalarWhereInput[]
    OR?: RiskAssessmentScalarWhereInput[]
    NOT?: RiskAssessmentScalarWhereInput | RiskAssessmentScalarWhereInput[]
    id?: IntFilter<"RiskAssessment"> | number
    createdAt?: DateTimeFilter<"RiskAssessment"> | Date | string
    updatedAt?: DateTimeFilter<"RiskAssessment"> | Date | string
    simulationId?: IntFilter<"RiskAssessment"> | number
    assessment?: JsonFilter<"RiskAssessment">
  }

  export type AuditLogUpsertWithWhereUniqueWithoutSimulationInput = {
    where: AuditLogWhereUniqueInput
    update: XOR<AuditLogUpdateWithoutSimulationInput, AuditLogUncheckedUpdateWithoutSimulationInput>
    create: XOR<AuditLogCreateWithoutSimulationInput, AuditLogUncheckedCreateWithoutSimulationInput>
  }

  export type AuditLogUpdateWithWhereUniqueWithoutSimulationInput = {
    where: AuditLogWhereUniqueInput
    data: XOR<AuditLogUpdateWithoutSimulationInput, AuditLogUncheckedUpdateWithoutSimulationInput>
  }

  export type AuditLogUpdateManyWithWhereWithoutSimulationInput = {
    where: AuditLogScalarWhereInput
    data: XOR<AuditLogUpdateManyMutationInput, AuditLogUncheckedUpdateManyWithoutSimulationInput>
  }

  export type SimulationCreateWithoutBiasDetectionResultInput = {
    createdAt?: Date | string
    updatedAt?: Date | string
    name: string
    description?: string | null
    status: $Enums.SimulationStatus
    config: JsonNullValueInput | InputJsonValue
    modelType: string
    version: string
    tags?: SimulationCreatetagsInput | string[]
    user: UserCreateNestedOneWithoutSimulationsInput
    FairnessAssessment?: FairnessAssessmentCreateNestedManyWithoutSimulationInput
    ExplainabilityAnalysis?: ExplainabilityAnalysisCreateNestedManyWithoutSimulationInput
    ComplianceRecord?: ComplianceRecordCreateNestedManyWithoutSimulationInput
    RiskAssessment?: RiskAssessmentCreateNestedManyWithoutSimulationInput
    auditLogs?: AuditLogCreateNestedManyWithoutSimulationInput
  }

  export type SimulationUncheckedCreateWithoutBiasDetectionResultInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    name: string
    description?: string | null
    status: $Enums.SimulationStatus
    userId: number
    config: JsonNullValueInput | InputJsonValue
    modelType: string
    version: string
    tags?: SimulationCreatetagsInput | string[]
    FairnessAssessment?: FairnessAssessmentUncheckedCreateNestedManyWithoutSimulationInput
    ExplainabilityAnalysis?: ExplainabilityAnalysisUncheckedCreateNestedManyWithoutSimulationInput
    ComplianceRecord?: ComplianceRecordUncheckedCreateNestedManyWithoutSimulationInput
    RiskAssessment?: RiskAssessmentUncheckedCreateNestedManyWithoutSimulationInput
    auditLogs?: AuditLogUncheckedCreateNestedManyWithoutSimulationInput
  }

  export type SimulationCreateOrConnectWithoutBiasDetectionResultInput = {
    where: SimulationWhereUniqueInput
    create: XOR<SimulationCreateWithoutBiasDetectionResultInput, SimulationUncheckedCreateWithoutBiasDetectionResultInput>
  }

  export type SimulationUpsertWithoutBiasDetectionResultInput = {
    update: XOR<SimulationUpdateWithoutBiasDetectionResultInput, SimulationUncheckedUpdateWithoutBiasDetectionResultInput>
    create: XOR<SimulationCreateWithoutBiasDetectionResultInput, SimulationUncheckedCreateWithoutBiasDetectionResultInput>
    where?: SimulationWhereInput
  }

  export type SimulationUpdateToOneWithWhereWithoutBiasDetectionResultInput = {
    where?: SimulationWhereInput
    data: XOR<SimulationUpdateWithoutBiasDetectionResultInput, SimulationUncheckedUpdateWithoutBiasDetectionResultInput>
  }

  export type SimulationUpdateWithoutBiasDetectionResultInput = {
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    name?: StringFieldUpdateOperationsInput | string
    description?: NullableStringFieldUpdateOperationsInput | string | null
    status?: EnumSimulationStatusFieldUpdateOperationsInput | $Enums.SimulationStatus
    config?: JsonNullValueInput | InputJsonValue
    modelType?: StringFieldUpdateOperationsInput | string
    version?: StringFieldUpdateOperationsInput | string
    tags?: SimulationUpdatetagsInput | string[]
    user?: UserUpdateOneRequiredWithoutSimulationsNestedInput
    FairnessAssessment?: FairnessAssessmentUpdateManyWithoutSimulationNestedInput
    ExplainabilityAnalysis?: ExplainabilityAnalysisUpdateManyWithoutSimulationNestedInput
    ComplianceRecord?: ComplianceRecordUpdateManyWithoutSimulationNestedInput
    RiskAssessment?: RiskAssessmentUpdateManyWithoutSimulationNestedInput
    auditLogs?: AuditLogUpdateManyWithoutSimulationNestedInput
  }

  export type SimulationUncheckedUpdateWithoutBiasDetectionResultInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    name?: StringFieldUpdateOperationsInput | string
    description?: NullableStringFieldUpdateOperationsInput | string | null
    status?: EnumSimulationStatusFieldUpdateOperationsInput | $Enums.SimulationStatus
    userId?: IntFieldUpdateOperationsInput | number
    config?: JsonNullValueInput | InputJsonValue
    modelType?: StringFieldUpdateOperationsInput | string
    version?: StringFieldUpdateOperationsInput | string
    tags?: SimulationUpdatetagsInput | string[]
    FairnessAssessment?: FairnessAssessmentUncheckedUpdateManyWithoutSimulationNestedInput
    ExplainabilityAnalysis?: ExplainabilityAnalysisUncheckedUpdateManyWithoutSimulationNestedInput
    ComplianceRecord?: ComplianceRecordUncheckedUpdateManyWithoutSimulationNestedInput
    RiskAssessment?: RiskAssessmentUncheckedUpdateManyWithoutSimulationNestedInput
    auditLogs?: AuditLogUncheckedUpdateManyWithoutSimulationNestedInput
  }

  export type SimulationCreateWithoutFairnessAssessmentInput = {
    createdAt?: Date | string
    updatedAt?: Date | string
    name: string
    description?: string | null
    status: $Enums.SimulationStatus
    config: JsonNullValueInput | InputJsonValue
    modelType: string
    version: string
    tags?: SimulationCreatetagsInput | string[]
    user: UserCreateNestedOneWithoutSimulationsInput
    BiasDetectionResult?: BiasDetectionResultCreateNestedManyWithoutSimulationInput
    ExplainabilityAnalysis?: ExplainabilityAnalysisCreateNestedManyWithoutSimulationInput
    ComplianceRecord?: ComplianceRecordCreateNestedManyWithoutSimulationInput
    RiskAssessment?: RiskAssessmentCreateNestedManyWithoutSimulationInput
    auditLogs?: AuditLogCreateNestedManyWithoutSimulationInput
  }

  export type SimulationUncheckedCreateWithoutFairnessAssessmentInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    name: string
    description?: string | null
    status: $Enums.SimulationStatus
    userId: number
    config: JsonNullValueInput | InputJsonValue
    modelType: string
    version: string
    tags?: SimulationCreatetagsInput | string[]
    BiasDetectionResult?: BiasDetectionResultUncheckedCreateNestedManyWithoutSimulationInput
    ExplainabilityAnalysis?: ExplainabilityAnalysisUncheckedCreateNestedManyWithoutSimulationInput
    ComplianceRecord?: ComplianceRecordUncheckedCreateNestedManyWithoutSimulationInput
    RiskAssessment?: RiskAssessmentUncheckedCreateNestedManyWithoutSimulationInput
    auditLogs?: AuditLogUncheckedCreateNestedManyWithoutSimulationInput
  }

  export type SimulationCreateOrConnectWithoutFairnessAssessmentInput = {
    where: SimulationWhereUniqueInput
    create: XOR<SimulationCreateWithoutFairnessAssessmentInput, SimulationUncheckedCreateWithoutFairnessAssessmentInput>
  }

  export type SimulationUpsertWithoutFairnessAssessmentInput = {
    update: XOR<SimulationUpdateWithoutFairnessAssessmentInput, SimulationUncheckedUpdateWithoutFairnessAssessmentInput>
    create: XOR<SimulationCreateWithoutFairnessAssessmentInput, SimulationUncheckedCreateWithoutFairnessAssessmentInput>
    where?: SimulationWhereInput
  }

  export type SimulationUpdateToOneWithWhereWithoutFairnessAssessmentInput = {
    where?: SimulationWhereInput
    data: XOR<SimulationUpdateWithoutFairnessAssessmentInput, SimulationUncheckedUpdateWithoutFairnessAssessmentInput>
  }

  export type SimulationUpdateWithoutFairnessAssessmentInput = {
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    name?: StringFieldUpdateOperationsInput | string
    description?: NullableStringFieldUpdateOperationsInput | string | null
    status?: EnumSimulationStatusFieldUpdateOperationsInput | $Enums.SimulationStatus
    config?: JsonNullValueInput | InputJsonValue
    modelType?: StringFieldUpdateOperationsInput | string
    version?: StringFieldUpdateOperationsInput | string
    tags?: SimulationUpdatetagsInput | string[]
    user?: UserUpdateOneRequiredWithoutSimulationsNestedInput
    BiasDetectionResult?: BiasDetectionResultUpdateManyWithoutSimulationNestedInput
    ExplainabilityAnalysis?: ExplainabilityAnalysisUpdateManyWithoutSimulationNestedInput
    ComplianceRecord?: ComplianceRecordUpdateManyWithoutSimulationNestedInput
    RiskAssessment?: RiskAssessmentUpdateManyWithoutSimulationNestedInput
    auditLogs?: AuditLogUpdateManyWithoutSimulationNestedInput
  }

  export type SimulationUncheckedUpdateWithoutFairnessAssessmentInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    name?: StringFieldUpdateOperationsInput | string
    description?: NullableStringFieldUpdateOperationsInput | string | null
    status?: EnumSimulationStatusFieldUpdateOperationsInput | $Enums.SimulationStatus
    userId?: IntFieldUpdateOperationsInput | number
    config?: JsonNullValueInput | InputJsonValue
    modelType?: StringFieldUpdateOperationsInput | string
    version?: StringFieldUpdateOperationsInput | string
    tags?: SimulationUpdatetagsInput | string[]
    BiasDetectionResult?: BiasDetectionResultUncheckedUpdateManyWithoutSimulationNestedInput
    ExplainabilityAnalysis?: ExplainabilityAnalysisUncheckedUpdateManyWithoutSimulationNestedInput
    ComplianceRecord?: ComplianceRecordUncheckedUpdateManyWithoutSimulationNestedInput
    RiskAssessment?: RiskAssessmentUncheckedUpdateManyWithoutSimulationNestedInput
    auditLogs?: AuditLogUncheckedUpdateManyWithoutSimulationNestedInput
  }

  export type SimulationCreateWithoutExplainabilityAnalysisInput = {
    createdAt?: Date | string
    updatedAt?: Date | string
    name: string
    description?: string | null
    status: $Enums.SimulationStatus
    config: JsonNullValueInput | InputJsonValue
    modelType: string
    version: string
    tags?: SimulationCreatetagsInput | string[]
    user: UserCreateNestedOneWithoutSimulationsInput
    BiasDetectionResult?: BiasDetectionResultCreateNestedManyWithoutSimulationInput
    FairnessAssessment?: FairnessAssessmentCreateNestedManyWithoutSimulationInput
    ComplianceRecord?: ComplianceRecordCreateNestedManyWithoutSimulationInput
    RiskAssessment?: RiskAssessmentCreateNestedManyWithoutSimulationInput
    auditLogs?: AuditLogCreateNestedManyWithoutSimulationInput
  }

  export type SimulationUncheckedCreateWithoutExplainabilityAnalysisInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    name: string
    description?: string | null
    status: $Enums.SimulationStatus
    userId: number
    config: JsonNullValueInput | InputJsonValue
    modelType: string
    version: string
    tags?: SimulationCreatetagsInput | string[]
    BiasDetectionResult?: BiasDetectionResultUncheckedCreateNestedManyWithoutSimulationInput
    FairnessAssessment?: FairnessAssessmentUncheckedCreateNestedManyWithoutSimulationInput
    ComplianceRecord?: ComplianceRecordUncheckedCreateNestedManyWithoutSimulationInput
    RiskAssessment?: RiskAssessmentUncheckedCreateNestedManyWithoutSimulationInput
    auditLogs?: AuditLogUncheckedCreateNestedManyWithoutSimulationInput
  }

  export type SimulationCreateOrConnectWithoutExplainabilityAnalysisInput = {
    where: SimulationWhereUniqueInput
    create: XOR<SimulationCreateWithoutExplainabilityAnalysisInput, SimulationUncheckedCreateWithoutExplainabilityAnalysisInput>
  }

  export type SimulationUpsertWithoutExplainabilityAnalysisInput = {
    update: XOR<SimulationUpdateWithoutExplainabilityAnalysisInput, SimulationUncheckedUpdateWithoutExplainabilityAnalysisInput>
    create: XOR<SimulationCreateWithoutExplainabilityAnalysisInput, SimulationUncheckedCreateWithoutExplainabilityAnalysisInput>
    where?: SimulationWhereInput
  }

  export type SimulationUpdateToOneWithWhereWithoutExplainabilityAnalysisInput = {
    where?: SimulationWhereInput
    data: XOR<SimulationUpdateWithoutExplainabilityAnalysisInput, SimulationUncheckedUpdateWithoutExplainabilityAnalysisInput>
  }

  export type SimulationUpdateWithoutExplainabilityAnalysisInput = {
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    name?: StringFieldUpdateOperationsInput | string
    description?: NullableStringFieldUpdateOperationsInput | string | null
    status?: EnumSimulationStatusFieldUpdateOperationsInput | $Enums.SimulationStatus
    config?: JsonNullValueInput | InputJsonValue
    modelType?: StringFieldUpdateOperationsInput | string
    version?: StringFieldUpdateOperationsInput | string
    tags?: SimulationUpdatetagsInput | string[]
    user?: UserUpdateOneRequiredWithoutSimulationsNestedInput
    BiasDetectionResult?: BiasDetectionResultUpdateManyWithoutSimulationNestedInput
    FairnessAssessment?: FairnessAssessmentUpdateManyWithoutSimulationNestedInput
    ComplianceRecord?: ComplianceRecordUpdateManyWithoutSimulationNestedInput
    RiskAssessment?: RiskAssessmentUpdateManyWithoutSimulationNestedInput
    auditLogs?: AuditLogUpdateManyWithoutSimulationNestedInput
  }

  export type SimulationUncheckedUpdateWithoutExplainabilityAnalysisInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    name?: StringFieldUpdateOperationsInput | string
    description?: NullableStringFieldUpdateOperationsInput | string | null
    status?: EnumSimulationStatusFieldUpdateOperationsInput | $Enums.SimulationStatus
    userId?: IntFieldUpdateOperationsInput | number
    config?: JsonNullValueInput | InputJsonValue
    modelType?: StringFieldUpdateOperationsInput | string
    version?: StringFieldUpdateOperationsInput | string
    tags?: SimulationUpdatetagsInput | string[]
    BiasDetectionResult?: BiasDetectionResultUncheckedUpdateManyWithoutSimulationNestedInput
    FairnessAssessment?: FairnessAssessmentUncheckedUpdateManyWithoutSimulationNestedInput
    ComplianceRecord?: ComplianceRecordUncheckedUpdateManyWithoutSimulationNestedInput
    RiskAssessment?: RiskAssessmentUncheckedUpdateManyWithoutSimulationNestedInput
    auditLogs?: AuditLogUncheckedUpdateManyWithoutSimulationNestedInput
  }

  export type SimulationCreateWithoutComplianceRecordInput = {
    createdAt?: Date | string
    updatedAt?: Date | string
    name: string
    description?: string | null
    status: $Enums.SimulationStatus
    config: JsonNullValueInput | InputJsonValue
    modelType: string
    version: string
    tags?: SimulationCreatetagsInput | string[]
    user: UserCreateNestedOneWithoutSimulationsInput
    BiasDetectionResult?: BiasDetectionResultCreateNestedManyWithoutSimulationInput
    FairnessAssessment?: FairnessAssessmentCreateNestedManyWithoutSimulationInput
    ExplainabilityAnalysis?: ExplainabilityAnalysisCreateNestedManyWithoutSimulationInput
    RiskAssessment?: RiskAssessmentCreateNestedManyWithoutSimulationInput
    auditLogs?: AuditLogCreateNestedManyWithoutSimulationInput
  }

  export type SimulationUncheckedCreateWithoutComplianceRecordInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    name: string
    description?: string | null
    status: $Enums.SimulationStatus
    userId: number
    config: JsonNullValueInput | InputJsonValue
    modelType: string
    version: string
    tags?: SimulationCreatetagsInput | string[]
    BiasDetectionResult?: BiasDetectionResultUncheckedCreateNestedManyWithoutSimulationInput
    FairnessAssessment?: FairnessAssessmentUncheckedCreateNestedManyWithoutSimulationInput
    ExplainabilityAnalysis?: ExplainabilityAnalysisUncheckedCreateNestedManyWithoutSimulationInput
    RiskAssessment?: RiskAssessmentUncheckedCreateNestedManyWithoutSimulationInput
    auditLogs?: AuditLogUncheckedCreateNestedManyWithoutSimulationInput
  }

  export type SimulationCreateOrConnectWithoutComplianceRecordInput = {
    where: SimulationWhereUniqueInput
    create: XOR<SimulationCreateWithoutComplianceRecordInput, SimulationUncheckedCreateWithoutComplianceRecordInput>
  }

  export type SimulationUpsertWithoutComplianceRecordInput = {
    update: XOR<SimulationUpdateWithoutComplianceRecordInput, SimulationUncheckedUpdateWithoutComplianceRecordInput>
    create: XOR<SimulationCreateWithoutComplianceRecordInput, SimulationUncheckedCreateWithoutComplianceRecordInput>
    where?: SimulationWhereInput
  }

  export type SimulationUpdateToOneWithWhereWithoutComplianceRecordInput = {
    where?: SimulationWhereInput
    data: XOR<SimulationUpdateWithoutComplianceRecordInput, SimulationUncheckedUpdateWithoutComplianceRecordInput>
  }

  export type SimulationUpdateWithoutComplianceRecordInput = {
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    name?: StringFieldUpdateOperationsInput | string
    description?: NullableStringFieldUpdateOperationsInput | string | null
    status?: EnumSimulationStatusFieldUpdateOperationsInput | $Enums.SimulationStatus
    config?: JsonNullValueInput | InputJsonValue
    modelType?: StringFieldUpdateOperationsInput | string
    version?: StringFieldUpdateOperationsInput | string
    tags?: SimulationUpdatetagsInput | string[]
    user?: UserUpdateOneRequiredWithoutSimulationsNestedInput
    BiasDetectionResult?: BiasDetectionResultUpdateManyWithoutSimulationNestedInput
    FairnessAssessment?: FairnessAssessmentUpdateManyWithoutSimulationNestedInput
    ExplainabilityAnalysis?: ExplainabilityAnalysisUpdateManyWithoutSimulationNestedInput
    RiskAssessment?: RiskAssessmentUpdateManyWithoutSimulationNestedInput
    auditLogs?: AuditLogUpdateManyWithoutSimulationNestedInput
  }

  export type SimulationUncheckedUpdateWithoutComplianceRecordInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    name?: StringFieldUpdateOperationsInput | string
    description?: NullableStringFieldUpdateOperationsInput | string | null
    status?: EnumSimulationStatusFieldUpdateOperationsInput | $Enums.SimulationStatus
    userId?: IntFieldUpdateOperationsInput | number
    config?: JsonNullValueInput | InputJsonValue
    modelType?: StringFieldUpdateOperationsInput | string
    version?: StringFieldUpdateOperationsInput | string
    tags?: SimulationUpdatetagsInput | string[]
    BiasDetectionResult?: BiasDetectionResultUncheckedUpdateManyWithoutSimulationNestedInput
    FairnessAssessment?: FairnessAssessmentUncheckedUpdateManyWithoutSimulationNestedInput
    ExplainabilityAnalysis?: ExplainabilityAnalysisUncheckedUpdateManyWithoutSimulationNestedInput
    RiskAssessment?: RiskAssessmentUncheckedUpdateManyWithoutSimulationNestedInput
    auditLogs?: AuditLogUncheckedUpdateManyWithoutSimulationNestedInput
  }

  export type SimulationCreateWithoutRiskAssessmentInput = {
    createdAt?: Date | string
    updatedAt?: Date | string
    name: string
    description?: string | null
    status: $Enums.SimulationStatus
    config: JsonNullValueInput | InputJsonValue
    modelType: string
    version: string
    tags?: SimulationCreatetagsInput | string[]
    user: UserCreateNestedOneWithoutSimulationsInput
    BiasDetectionResult?: BiasDetectionResultCreateNestedManyWithoutSimulationInput
    FairnessAssessment?: FairnessAssessmentCreateNestedManyWithoutSimulationInput
    ExplainabilityAnalysis?: ExplainabilityAnalysisCreateNestedManyWithoutSimulationInput
    ComplianceRecord?: ComplianceRecordCreateNestedManyWithoutSimulationInput
    auditLogs?: AuditLogCreateNestedManyWithoutSimulationInput
  }

  export type SimulationUncheckedCreateWithoutRiskAssessmentInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    name: string
    description?: string | null
    status: $Enums.SimulationStatus
    userId: number
    config: JsonNullValueInput | InputJsonValue
    modelType: string
    version: string
    tags?: SimulationCreatetagsInput | string[]
    BiasDetectionResult?: BiasDetectionResultUncheckedCreateNestedManyWithoutSimulationInput
    FairnessAssessment?: FairnessAssessmentUncheckedCreateNestedManyWithoutSimulationInput
    ExplainabilityAnalysis?: ExplainabilityAnalysisUncheckedCreateNestedManyWithoutSimulationInput
    ComplianceRecord?: ComplianceRecordUncheckedCreateNestedManyWithoutSimulationInput
    auditLogs?: AuditLogUncheckedCreateNestedManyWithoutSimulationInput
  }

  export type SimulationCreateOrConnectWithoutRiskAssessmentInput = {
    where: SimulationWhereUniqueInput
    create: XOR<SimulationCreateWithoutRiskAssessmentInput, SimulationUncheckedCreateWithoutRiskAssessmentInput>
  }

  export type SimulationUpsertWithoutRiskAssessmentInput = {
    update: XOR<SimulationUpdateWithoutRiskAssessmentInput, SimulationUncheckedUpdateWithoutRiskAssessmentInput>
    create: XOR<SimulationCreateWithoutRiskAssessmentInput, SimulationUncheckedCreateWithoutRiskAssessmentInput>
    where?: SimulationWhereInput
  }

  export type SimulationUpdateToOneWithWhereWithoutRiskAssessmentInput = {
    where?: SimulationWhereInput
    data: XOR<SimulationUpdateWithoutRiskAssessmentInput, SimulationUncheckedUpdateWithoutRiskAssessmentInput>
  }

  export type SimulationUpdateWithoutRiskAssessmentInput = {
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    name?: StringFieldUpdateOperationsInput | string
    description?: NullableStringFieldUpdateOperationsInput | string | null
    status?: EnumSimulationStatusFieldUpdateOperationsInput | $Enums.SimulationStatus
    config?: JsonNullValueInput | InputJsonValue
    modelType?: StringFieldUpdateOperationsInput | string
    version?: StringFieldUpdateOperationsInput | string
    tags?: SimulationUpdatetagsInput | string[]
    user?: UserUpdateOneRequiredWithoutSimulationsNestedInput
    BiasDetectionResult?: BiasDetectionResultUpdateManyWithoutSimulationNestedInput
    FairnessAssessment?: FairnessAssessmentUpdateManyWithoutSimulationNestedInput
    ExplainabilityAnalysis?: ExplainabilityAnalysisUpdateManyWithoutSimulationNestedInput
    ComplianceRecord?: ComplianceRecordUpdateManyWithoutSimulationNestedInput
    auditLogs?: AuditLogUpdateManyWithoutSimulationNestedInput
  }

  export type SimulationUncheckedUpdateWithoutRiskAssessmentInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    name?: StringFieldUpdateOperationsInput | string
    description?: NullableStringFieldUpdateOperationsInput | string | null
    status?: EnumSimulationStatusFieldUpdateOperationsInput | $Enums.SimulationStatus
    userId?: IntFieldUpdateOperationsInput | number
    config?: JsonNullValueInput | InputJsonValue
    modelType?: StringFieldUpdateOperationsInput | string
    version?: StringFieldUpdateOperationsInput | string
    tags?: SimulationUpdatetagsInput | string[]
    BiasDetectionResult?: BiasDetectionResultUncheckedUpdateManyWithoutSimulationNestedInput
    FairnessAssessment?: FairnessAssessmentUncheckedUpdateManyWithoutSimulationNestedInput
    ExplainabilityAnalysis?: ExplainabilityAnalysisUncheckedUpdateManyWithoutSimulationNestedInput
    ComplianceRecord?: ComplianceRecordUncheckedUpdateManyWithoutSimulationNestedInput
    auditLogs?: AuditLogUncheckedUpdateManyWithoutSimulationNestedInput
  }

  export type UserCreateWithoutAuditLogsInput = {
    createdAt?: Date | string
    updatedAt?: Date | string
    email: string
    passwordHash: string
    name: string
    role?: string
    simulations?: SimulationCreateNestedManyWithoutUserInput
  }

  export type UserUncheckedCreateWithoutAuditLogsInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    email: string
    passwordHash: string
    name: string
    role?: string
    simulations?: SimulationUncheckedCreateNestedManyWithoutUserInput
  }

  export type UserCreateOrConnectWithoutAuditLogsInput = {
    where: UserWhereUniqueInput
    create: XOR<UserCreateWithoutAuditLogsInput, UserUncheckedCreateWithoutAuditLogsInput>
  }

  export type SimulationCreateWithoutAuditLogsInput = {
    createdAt?: Date | string
    updatedAt?: Date | string
    name: string
    description?: string | null
    status: $Enums.SimulationStatus
    config: JsonNullValueInput | InputJsonValue
    modelType: string
    version: string
    tags?: SimulationCreatetagsInput | string[]
    user: UserCreateNestedOneWithoutSimulationsInput
    BiasDetectionResult?: BiasDetectionResultCreateNestedManyWithoutSimulationInput
    FairnessAssessment?: FairnessAssessmentCreateNestedManyWithoutSimulationInput
    ExplainabilityAnalysis?: ExplainabilityAnalysisCreateNestedManyWithoutSimulationInput
    ComplianceRecord?: ComplianceRecordCreateNestedManyWithoutSimulationInput
    RiskAssessment?: RiskAssessmentCreateNestedManyWithoutSimulationInput
  }

  export type SimulationUncheckedCreateWithoutAuditLogsInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    name: string
    description?: string | null
    status: $Enums.SimulationStatus
    userId: number
    config: JsonNullValueInput | InputJsonValue
    modelType: string
    version: string
    tags?: SimulationCreatetagsInput | string[]
    BiasDetectionResult?: BiasDetectionResultUncheckedCreateNestedManyWithoutSimulationInput
    FairnessAssessment?: FairnessAssessmentUncheckedCreateNestedManyWithoutSimulationInput
    ExplainabilityAnalysis?: ExplainabilityAnalysisUncheckedCreateNestedManyWithoutSimulationInput
    ComplianceRecord?: ComplianceRecordUncheckedCreateNestedManyWithoutSimulationInput
    RiskAssessment?: RiskAssessmentUncheckedCreateNestedManyWithoutSimulationInput
  }

  export type SimulationCreateOrConnectWithoutAuditLogsInput = {
    where: SimulationWhereUniqueInput
    create: XOR<SimulationCreateWithoutAuditLogsInput, SimulationUncheckedCreateWithoutAuditLogsInput>
  }

  export type UserUpsertWithoutAuditLogsInput = {
    update: XOR<UserUpdateWithoutAuditLogsInput, UserUncheckedUpdateWithoutAuditLogsInput>
    create: XOR<UserCreateWithoutAuditLogsInput, UserUncheckedCreateWithoutAuditLogsInput>
    where?: UserWhereInput
  }

  export type UserUpdateToOneWithWhereWithoutAuditLogsInput = {
    where?: UserWhereInput
    data: XOR<UserUpdateWithoutAuditLogsInput, UserUncheckedUpdateWithoutAuditLogsInput>
  }

  export type UserUpdateWithoutAuditLogsInput = {
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    email?: StringFieldUpdateOperationsInput | string
    passwordHash?: StringFieldUpdateOperationsInput | string
    name?: StringFieldUpdateOperationsInput | string
    role?: StringFieldUpdateOperationsInput | string
    simulations?: SimulationUpdateManyWithoutUserNestedInput
  }

  export type UserUncheckedUpdateWithoutAuditLogsInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    email?: StringFieldUpdateOperationsInput | string
    passwordHash?: StringFieldUpdateOperationsInput | string
    name?: StringFieldUpdateOperationsInput | string
    role?: StringFieldUpdateOperationsInput | string
    simulations?: SimulationUncheckedUpdateManyWithoutUserNestedInput
  }

  export type SimulationUpsertWithoutAuditLogsInput = {
    update: XOR<SimulationUpdateWithoutAuditLogsInput, SimulationUncheckedUpdateWithoutAuditLogsInput>
    create: XOR<SimulationCreateWithoutAuditLogsInput, SimulationUncheckedCreateWithoutAuditLogsInput>
    where?: SimulationWhereInput
  }

  export type SimulationUpdateToOneWithWhereWithoutAuditLogsInput = {
    where?: SimulationWhereInput
    data: XOR<SimulationUpdateWithoutAuditLogsInput, SimulationUncheckedUpdateWithoutAuditLogsInput>
  }

  export type SimulationUpdateWithoutAuditLogsInput = {
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    name?: StringFieldUpdateOperationsInput | string
    description?: NullableStringFieldUpdateOperationsInput | string | null
    status?: EnumSimulationStatusFieldUpdateOperationsInput | $Enums.SimulationStatus
    config?: JsonNullValueInput | InputJsonValue
    modelType?: StringFieldUpdateOperationsInput | string
    version?: StringFieldUpdateOperationsInput | string
    tags?: SimulationUpdatetagsInput | string[]
    user?: UserUpdateOneRequiredWithoutSimulationsNestedInput
    BiasDetectionResult?: BiasDetectionResultUpdateManyWithoutSimulationNestedInput
    FairnessAssessment?: FairnessAssessmentUpdateManyWithoutSimulationNestedInput
    ExplainabilityAnalysis?: ExplainabilityAnalysisUpdateManyWithoutSimulationNestedInput
    ComplianceRecord?: ComplianceRecordUpdateManyWithoutSimulationNestedInput
    RiskAssessment?: RiskAssessmentUpdateManyWithoutSimulationNestedInput
  }

  export type SimulationUncheckedUpdateWithoutAuditLogsInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    name?: StringFieldUpdateOperationsInput | string
    description?: NullableStringFieldUpdateOperationsInput | string | null
    status?: EnumSimulationStatusFieldUpdateOperationsInput | $Enums.SimulationStatus
    userId?: IntFieldUpdateOperationsInput | number
    config?: JsonNullValueInput | InputJsonValue
    modelType?: StringFieldUpdateOperationsInput | string
    version?: StringFieldUpdateOperationsInput | string
    tags?: SimulationUpdatetagsInput | string[]
    BiasDetectionResult?: BiasDetectionResultUncheckedUpdateManyWithoutSimulationNestedInput
    FairnessAssessment?: FairnessAssessmentUncheckedUpdateManyWithoutSimulationNestedInput
    ExplainabilityAnalysis?: ExplainabilityAnalysisUncheckedUpdateManyWithoutSimulationNestedInput
    ComplianceRecord?: ComplianceRecordUncheckedUpdateManyWithoutSimulationNestedInput
    RiskAssessment?: RiskAssessmentUncheckedUpdateManyWithoutSimulationNestedInput
  }

  export type SimulationCreateManyUserInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    name: string
    description?: string | null
    status: $Enums.SimulationStatus
    config: JsonNullValueInput | InputJsonValue
    modelType: string
    version: string
    tags?: SimulationCreatetagsInput | string[]
  }

  export type AuditLogCreateManyUserInput = {
    id?: number
    createdAt?: Date | string
    simulationId?: number | null
    action: string
    details: JsonNullValueInput | InputJsonValue
    ipAddress: string
    userAgent: string
  }

  export type SimulationUpdateWithoutUserInput = {
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    name?: StringFieldUpdateOperationsInput | string
    description?: NullableStringFieldUpdateOperationsInput | string | null
    status?: EnumSimulationStatusFieldUpdateOperationsInput | $Enums.SimulationStatus
    config?: JsonNullValueInput | InputJsonValue
    modelType?: StringFieldUpdateOperationsInput | string
    version?: StringFieldUpdateOperationsInput | string
    tags?: SimulationUpdatetagsInput | string[]
    BiasDetectionResult?: BiasDetectionResultUpdateManyWithoutSimulationNestedInput
    FairnessAssessment?: FairnessAssessmentUpdateManyWithoutSimulationNestedInput
    ExplainabilityAnalysis?: ExplainabilityAnalysisUpdateManyWithoutSimulationNestedInput
    ComplianceRecord?: ComplianceRecordUpdateManyWithoutSimulationNestedInput
    RiskAssessment?: RiskAssessmentUpdateManyWithoutSimulationNestedInput
    auditLogs?: AuditLogUpdateManyWithoutSimulationNestedInput
  }

  export type SimulationUncheckedUpdateWithoutUserInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    name?: StringFieldUpdateOperationsInput | string
    description?: NullableStringFieldUpdateOperationsInput | string | null
    status?: EnumSimulationStatusFieldUpdateOperationsInput | $Enums.SimulationStatus
    config?: JsonNullValueInput | InputJsonValue
    modelType?: StringFieldUpdateOperationsInput | string
    version?: StringFieldUpdateOperationsInput | string
    tags?: SimulationUpdatetagsInput | string[]
    BiasDetectionResult?: BiasDetectionResultUncheckedUpdateManyWithoutSimulationNestedInput
    FairnessAssessment?: FairnessAssessmentUncheckedUpdateManyWithoutSimulationNestedInput
    ExplainabilityAnalysis?: ExplainabilityAnalysisUncheckedUpdateManyWithoutSimulationNestedInput
    ComplianceRecord?: ComplianceRecordUncheckedUpdateManyWithoutSimulationNestedInput
    RiskAssessment?: RiskAssessmentUncheckedUpdateManyWithoutSimulationNestedInput
    auditLogs?: AuditLogUncheckedUpdateManyWithoutSimulationNestedInput
  }

  export type SimulationUncheckedUpdateManyWithoutUserInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    name?: StringFieldUpdateOperationsInput | string
    description?: NullableStringFieldUpdateOperationsInput | string | null
    status?: EnumSimulationStatusFieldUpdateOperationsInput | $Enums.SimulationStatus
    config?: JsonNullValueInput | InputJsonValue
    modelType?: StringFieldUpdateOperationsInput | string
    version?: StringFieldUpdateOperationsInput | string
    tags?: SimulationUpdatetagsInput | string[]
  }

  export type AuditLogUpdateWithoutUserInput = {
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    action?: StringFieldUpdateOperationsInput | string
    details?: JsonNullValueInput | InputJsonValue
    ipAddress?: StringFieldUpdateOperationsInput | string
    userAgent?: StringFieldUpdateOperationsInput | string
    simulation?: SimulationUpdateOneWithoutAuditLogsNestedInput
  }

  export type AuditLogUncheckedUpdateWithoutUserInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    simulationId?: NullableIntFieldUpdateOperationsInput | number | null
    action?: StringFieldUpdateOperationsInput | string
    details?: JsonNullValueInput | InputJsonValue
    ipAddress?: StringFieldUpdateOperationsInput | string
    userAgent?: StringFieldUpdateOperationsInput | string
  }

  export type AuditLogUncheckedUpdateManyWithoutUserInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    simulationId?: NullableIntFieldUpdateOperationsInput | number | null
    action?: StringFieldUpdateOperationsInput | string
    details?: JsonNullValueInput | InputJsonValue
    ipAddress?: StringFieldUpdateOperationsInput | string
    userAgent?: StringFieldUpdateOperationsInput | string
  }

  export type BiasDetectionResultCreateManySimulationInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    result: JsonNullValueInput | InputJsonValue
  }

  export type FairnessAssessmentCreateManySimulationInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    assessment: JsonNullValueInput | InputJsonValue
  }

  export type ExplainabilityAnalysisCreateManySimulationInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    analysis: JsonNullValueInput | InputJsonValue
  }

  export type ComplianceRecordCreateManySimulationInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    record: JsonNullValueInput | InputJsonValue
  }

  export type RiskAssessmentCreateManySimulationInput = {
    id?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    assessment: JsonNullValueInput | InputJsonValue
  }

  export type AuditLogCreateManySimulationInput = {
    id?: number
    createdAt?: Date | string
    userId: number
    action: string
    details: JsonNullValueInput | InputJsonValue
    ipAddress: string
    userAgent: string
  }

  export type BiasDetectionResultUpdateWithoutSimulationInput = {
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    result?: JsonNullValueInput | InputJsonValue
  }

  export type BiasDetectionResultUncheckedUpdateWithoutSimulationInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    result?: JsonNullValueInput | InputJsonValue
  }

  export type BiasDetectionResultUncheckedUpdateManyWithoutSimulationInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    result?: JsonNullValueInput | InputJsonValue
  }

  export type FairnessAssessmentUpdateWithoutSimulationInput = {
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    assessment?: JsonNullValueInput | InputJsonValue
  }

  export type FairnessAssessmentUncheckedUpdateWithoutSimulationInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    assessment?: JsonNullValueInput | InputJsonValue
  }

  export type FairnessAssessmentUncheckedUpdateManyWithoutSimulationInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    assessment?: JsonNullValueInput | InputJsonValue
  }

  export type ExplainabilityAnalysisUpdateWithoutSimulationInput = {
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    analysis?: JsonNullValueInput | InputJsonValue
  }

  export type ExplainabilityAnalysisUncheckedUpdateWithoutSimulationInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    analysis?: JsonNullValueInput | InputJsonValue
  }

  export type ExplainabilityAnalysisUncheckedUpdateManyWithoutSimulationInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    analysis?: JsonNullValueInput | InputJsonValue
  }

  export type ComplianceRecordUpdateWithoutSimulationInput = {
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    record?: JsonNullValueInput | InputJsonValue
  }

  export type ComplianceRecordUncheckedUpdateWithoutSimulationInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    record?: JsonNullValueInput | InputJsonValue
  }

  export type ComplianceRecordUncheckedUpdateManyWithoutSimulationInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    record?: JsonNullValueInput | InputJsonValue
  }

  export type RiskAssessmentUpdateWithoutSimulationInput = {
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    assessment?: JsonNullValueInput | InputJsonValue
  }

  export type RiskAssessmentUncheckedUpdateWithoutSimulationInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    assessment?: JsonNullValueInput | InputJsonValue
  }

  export type RiskAssessmentUncheckedUpdateManyWithoutSimulationInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    assessment?: JsonNullValueInput | InputJsonValue
  }

  export type AuditLogUpdateWithoutSimulationInput = {
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    action?: StringFieldUpdateOperationsInput | string
    details?: JsonNullValueInput | InputJsonValue
    ipAddress?: StringFieldUpdateOperationsInput | string
    userAgent?: StringFieldUpdateOperationsInput | string
    user?: UserUpdateOneRequiredWithoutAuditLogsNestedInput
  }

  export type AuditLogUncheckedUpdateWithoutSimulationInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    userId?: IntFieldUpdateOperationsInput | number
    action?: StringFieldUpdateOperationsInput | string
    details?: JsonNullValueInput | InputJsonValue
    ipAddress?: StringFieldUpdateOperationsInput | string
    userAgent?: StringFieldUpdateOperationsInput | string
  }

  export type AuditLogUncheckedUpdateManyWithoutSimulationInput = {
    id?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    userId?: IntFieldUpdateOperationsInput | number
    action?: StringFieldUpdateOperationsInput | string
    details?: JsonNullValueInput | InputJsonValue
    ipAddress?: StringFieldUpdateOperationsInput | string
    userAgent?: StringFieldUpdateOperationsInput | string
  }



  /**
   * Batch Payload for updateMany & deleteMany & createMany
   */

  export type BatchPayload = {
    count: number
  }

  /**
   * DMMF
   */
  export const dmmf: runtime.BaseDMMF
}